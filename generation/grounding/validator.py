"""Deterministic grounding validator and entity containment auditor.

Validates generated answers strictly against the evidence supplied to generation,
evaluating entity containment, important token overlap, and sentence-level
support approximations without speculative claims of complete semantic proof.
"""
from __future__ import annotations



import re
from collections.abc import Sequence

from app.config.settings import get_settings
from generation.grounding.entities import AcademicEntityExtractor
from generation.models import (
    ConflictReport,
    GroundingValidationResult,
    RetrievedEvidence,
)
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK


class GroundingValidator:
    """Audits generated answers against generation evidence for groundedness and entity containment.

    Core capabilities:
    1. Entity Containment: Verifies all academic entities (codes, regulations, dates, years)
       in the answer exist verbatim or normalized in the supplied evidence.
    2. Statement Support: Approximates whether each answer sentence is supported by an
       evidence sentence containing overlapping terms and co-occurring entities.
    3. Strict Remediation: Safely trims unsupported claims or triggers standardized no-answer.
    """

    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "if", "then", "else", "when", "at",
        "from", "by", "for", "with", "about", "against", "between", "into", "through",
        "during", "before", "after", "above", "below", "to", "of", "up", "down",
        "in", "out", "on", "off", "over", "under", "again", "further", "once", "here", "there", "all", "any", "both", "each", "few", "more", "most",
        "other", "some", "such", "no", "nor", "not", "only", "own", "same", "so",
        "than", "too", "very", "s", "t", "can", "will", "just", "don", "should",
        "now", "is", "are", "was", "were", "be", "been", "being", "have", "has",
        "had", "do", "does", "did", "as", "university", "official", "based", "this",
    }

    def __init__(
        self,
        strict_mode: bool | None = None,
        min_token_overlap: float | None = None,
    ):
        settings = get_settings()
        self.strict_mode = strict_mode if strict_mode is not None else settings.grounding_strict_mode
        self.min_token_overlap = (
            min_token_overlap if min_token_overlap is not None else settings.grounding_min_token_overlap
        )

    def validate(
        self,
        answer: str,
        evidence_items: Sequence[RetrievedEvidence],
        conflict_report: ConflictReport | None = None,
    ) -> tuple[GroundingValidationResult, str]:
        """Audit the answer against generation evidence and return (validation_result, final_answer).

        If strict mode is enabled and ungrounded entities or unsupported statements are found,
        the answer will be deterministically remediated or replaced with the standardized fallback.
        """
        cleaned_answer = answer.strip()

        # If answer is already the standardized fallback, it is by definition grounded in no-answer
        if cleaned_answer == INSUFFICIENT_EVIDENCE_FALLBACK:
            return (
                GroundingValidationResult(
                    is_grounded=True,
                    faithfulness_score=1.0,
                    ungrounded_entities=[],
                    supported_statements_count=1,
                    unsupported_statements_count=0,
                    entity_coverage=1.0,
                    token_overlap=1.0,
                    statement_support=1.0,
                    conflict_report=conflict_report,
                    remediation_applied=False,
                ),
                cleaned_answer,
            )

        if not evidence_items:
            # Answer provided with zero evidence is ungrounded
            return self._handle_ungrounded(
                answer=cleaned_answer,
                ungrounded_entities=["No evidence provided"],
                supported_count=0,
                unsupported_count=1,
                entity_cov=0.0,
                token_cov=0.0,
                stmt_sup=0.0,
                conflict_report=conflict_report,
            )

        # 1. Combine all evidence text
        evidence_texts = [ev.text for ev in evidence_items]
        combined_evidence = " ".join(evidence_texts)
        evidence_entities = AcademicEntityExtractor.extract_entities(combined_evidence)
        evidence_entity_norm_keys = {(e.entity_type, e.normalized_entity) for e in evidence_entities}
        evidence_tokens = self._tokenize(combined_evidence)

        # 2. Extract answer entities
        answer_entities = AcademicEntityExtractor.extract_entities(cleaned_answer)
        ungrounded_entities: list[str] = []

        for ae in answer_entities:
            key = (ae.entity_type, ae.normalized_entity)
            if key not in evidence_entity_norm_keys:
                ungrounded_entities.append(f"{ae.entity_type}:{ae.raw_entity}")

        if answer_entities:
            entity_coverage = (len(answer_entities) - len(ungrounded_entities)) / len(answer_entities)
        else:
            entity_coverage = 1.0

        # 3. Check token overlap between answer and evidence
        answer_tokens = self._tokenize(cleaned_answer)
        for ae in answer_entities:
            answer_tokens.update(self._tokenize(ae.normalized_entity))
        for ee in evidence_entities:
            evidence_tokens.update(self._tokenize(ee.normalized_entity))

        if answer_tokens:
            common_tokens = answer_tokens.intersection(evidence_tokens)
            token_overlap = len(common_tokens) / len(answer_tokens)
        else:
            token_overlap = 1.0

        # 4. Check statement-level support approximation
        statements = self._split_into_statements(cleaned_answer)
        supported_statements: list[str] = []
        unsupported_statements: list[str] = []

        for stmt in statements:
            if self._is_statement_supported(stmt, evidence_items):
                supported_statements.append(stmt)
            else:
                unsupported_statements.append(stmt)

        total_stmts = len(statements) if statements else 1
        supported_count = len(supported_statements)
        unsupported_count = len(unsupported_statements)
        statement_support = supported_count / total_stmts

        # 5. Deterministic scoring approximation formula:
        faithfulness_score = round(
            0.4 * entity_coverage + 0.3 * statement_support + 0.3 * token_overlap,
            4,
        )
        faithfulness_score = max(0.0, min(1.0, faithfulness_score))

        is_grounded = (len(ungrounded_entities) == 0) and (statement_support >= 0.5)

        # 6. Apply Strict / Non-Strict Remediation Policy
        if not is_grounded and self.strict_mode:
            # Strict mode: remediate or fall back
            clean_supported_statements: list[str] = []
            for stmt in supported_statements:
                stmt_ents = AcademicEntityExtractor.extract_entities(stmt)
                stmt_has_ungrounded = any(
                    f"{e.entity_type}:{e.raw_entity}" in ungrounded_entities for e in stmt_ents
                )
                if not stmt_has_ungrounded:
                    clean_supported_statements.append(stmt)

            if clean_supported_statements:
                # Safe remediation: preserve only clean supported statements
                remediated_answer = "\n".join(
                    f"- {s}" if not s.startswith("-") else s for s in clean_supported_statements
                )
                return (
                    GroundingValidationResult(
                        is_grounded=True,
                        faithfulness_score=faithfulness_score,
                        ungrounded_entities=[],
                        supported_statements_count=len(clean_supported_statements),
                        unsupported_statements_count=0,
                        entity_coverage=1.0,
                        token_overlap=token_overlap,
                        statement_support=1.0,
                        conflict_report=conflict_report,
                        remediation_applied=True,
                    ),
                    remediated_answer,
                )
            else:
                # Unsafe remediation or all statements ungrounded: strictly return standardized fallback
                return (
                    GroundingValidationResult(
                        is_grounded=False,
                        faithfulness_score=0.0,
                        ungrounded_entities=ungrounded_entities,
                        supported_statements_count=0,
                        unsupported_statements_count=total_stmts,
                        entity_coverage=entity_coverage,
                        token_overlap=token_overlap,
                        statement_support=0.0,
                        conflict_report=conflict_report,
                        remediation_applied=True,
                    ),
                    INSUFFICIENT_EVIDENCE_FALLBACK,
                )

        # Non-strict mode or fully grounded
        return (
            GroundingValidationResult(
                is_grounded=is_grounded,
                faithfulness_score=faithfulness_score,
                ungrounded_entities=ungrounded_entities,
                supported_statements_count=supported_count,
                unsupported_statements_count=unsupported_count,
                entity_coverage=round(entity_coverage, 4),
                token_overlap=round(token_overlap, 4),
                statement_support=round(statement_support, 4),
                conflict_report=conflict_report,
                remediation_applied=False,
            ),
            cleaned_answer,
        )

    def _is_statement_supported(self, statement: str, evidence_items: Sequence[RetrievedEvidence]) -> bool:
        """Check if a statement is supported by at least one evidence chunk with co-occurring entities."""
        stmt_tokens = self._tokenize(statement)
        stmt_entities = AcademicEntityExtractor.extract_entities(statement)
        stmt_entity_keys = {(e.entity_type, e.normalized_entity) for e in stmt_entities}

        for ev in evidence_items:
            ev_tokens = self._tokenize(ev.text)
            overlap = len(stmt_tokens.intersection(ev_tokens)) / len(stmt_tokens) if stmt_tokens else 1.0
            ev_entities = AcademicEntityExtractor.extract_entities(ev.text)
            ev_entity_keys = {(e.entity_type, e.normalized_entity) for e in ev_entities}

            # If all statement entities are in this evidence chunk:
            if stmt_entity_keys and stmt_entity_keys.issubset(ev_entity_keys):
                if overlap >= self.min_token_overlap or len(stmt_tokens) <= 3:
                    return True

            if overlap >= self.min_token_overlap and not stmt_entity_keys:
                return True

        return False

    def _split_into_statements(self, text: str) -> list[str]:
        """Split text into individual factual statement units."""
        lines = [re.sub(r"^[- *•\s]+", "", line).strip() for line in text.splitlines() if line.strip()]
        statements: list[str] = []
        for line in lines:
            sentences = re.split(r"(?<=[.!?])\s+", line)
            for s in sentences:
                s_clean = s.strip()
                if len(s_clean) > 5 and not s_clean.lower().startswith("based on the official"):
                    statements.append(s_clean)
        return statements if statements else [text]

    def _tokenize(self, text: str) -> set[str]:
        """Tokenize text into content words excluding stopwords."""
        words = re.findall(r"\b[a-zA-Z0-9_\-]{2,}\b", text.lower())
        return {w for w in words if w not in self.STOPWORDS}

    def _handle_ungrounded(
        self,
        answer: str,
        ungrounded_entities: list[str],
        supported_count: int,
        unsupported_count: int,
        entity_cov: float,
        token_cov: float,
        stmt_sup: float,
        conflict_report: ConflictReport | None,
    ) -> tuple[GroundingValidationResult, str]:
        """Helper to process ungrounded result in strict vs non-strict mode."""
        if self.strict_mode:
            return (
                GroundingValidationResult(
                    is_grounded=False,
                    faithfulness_score=0.0,
                    ungrounded_entities=ungrounded_entities,
                    supported_statements_count=0,
                    unsupported_statements_count=unsupported_count,
                    entity_coverage=0.0,
                    token_overlap=0.0,
                    statement_support=0.0,
                    conflict_report=conflict_report,
                    remediation_applied=True,
                ),
                INSUFFICIENT_EVIDENCE_FALLBACK,
            )
        return (
            GroundingValidationResult(
                is_grounded=False,
                faithfulness_score=0.0,
                ungrounded_entities=ungrounded_entities,
                supported_statements_count=supported_count,
                unsupported_statements_count=unsupported_count,
                entity_coverage=entity_cov,
                token_overlap=token_cov,
                statement_support=stmt_sup,
                conflict_report=conflict_report,
                remediation_applied=False,
            ),
            answer,
        )
