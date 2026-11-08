"""Deterministic citation verification and factual claim-evidence audit subsystem."""

import re
import time
from typing import ClassVar

from citations.models import CitationItem, CitationVerificationResult, ClaimItem
from generation.grounding.entities import AcademicEntityExtractor
from generation.models import RetrievedEvidence


class CitationVerifier:
    """Deterministic auditor evaluating whether generated factual claims are factually supported by cited chunks.

    Guarantees:
    - Verifies academic entity containment (course codes, regulations, dates, exam types).
    - Verifies numeric/percentage precision (75% attendance, 24 credits, 5.0 CGPA).
    - Verifies substantive lexical alignment and predicate/subject co-occurrence.
    - Prevents false-positive entity-only verification (e.g. course code mentioned without exam date).
    - Calculates operational metrics: Citation Precision, Citation Recall, and Overall Support Score.
    """

    STOPWORDS: ClassVar[set[str]] = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
        "by", "about", "as", "into", "through", "during", "before", "after", "above",
        "below", "from", "up", "down", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "of", "this", "that",
        "these", "those", "it", "its", "they", "them", "their", "will", "would",
        "shall", "should", "may", "might", "must", "can", "could", "also", "each",
        "all", "any", "both", "such", "not", "only", "same", "so", "than", "too",
    }

    def __init__(
        self,
        min_support_score: float = 0.50,
        require_exact_entities: bool = True,
    ) -> None:
        self.min_support_score = min_support_score
        self.require_exact_entities = require_exact_entities

    def verify_citations(
        self,
        claims: list[ClaimItem],
        citations: list[CitationItem],
        evidence_items: list[RetrievedEvidence],
    ) -> CitationVerificationResult:
        """Audit all claims and citations against generation evidence and compute verification metrics."""
        t_0 = time.perf_counter()

        if not claims and not citations:
            return CitationVerificationResult(
                is_fully_supported=True,
                overall_support_score=1.0,
                citation_precision=1.0,
                citation_recall=1.0,
                claims=[],
                citations=[],
                unsupported_claims=[],
                unverified_citations=[],
                verification_latency_ms=0.0,
            )

        chunk_by_id: dict[str, RetrievedEvidence] = {ev.chunk_id: ev for ev in evidence_items}
        cit_by_id: dict[str, CitationItem] = {c.citation_id: c for c in citations}

        audited_citations: dict[str, CitationItem] = {}
        audited_claims: list[ClaimItem] = []
        unsupported_claims: list[str] = []

        # Audit each claim against its associated citations
        for claim in claims:
            if not claim.associated_citation_ids:
                audited_claims.append(
                    claim.model_copy(
                        update={
                            "is_supported": False,
                            "support_score": 0.0,
                        }
                    )
                )
                unsupported_claims.append(claim.claim_text)
                continue

            # Gather text of all chunks cited for this claim
            cited_chunks: list[RetrievedEvidence] = []
            for cit_id in claim.associated_citation_ids:
                if cit_id in cit_by_id:
                    c_item = cit_by_id[cit_id]
                    if c_item.chunk_id in chunk_by_id:
                        cited_chunks.append(chunk_by_id[c_item.chunk_id])

            if not cited_chunks:
                audited_claims.append(
                    claim.model_copy(
                        update={
                            "is_supported": False,
                            "support_score": 0.0,
                        }
                    )
                )
                unsupported_claims.append(claim.claim_text)
                continue

            # Evaluate support for this claim against combined cited evidence
            combined_evidence_text = "\n".join(c.text for c in cited_chunks)
            claim_support_score, is_claim_supported = self._evaluate_support(
                claim_text=claim.claim_text,
                evidence_text=combined_evidence_text,
            )

            # Audit individual citations supporting this claim
            for cit_id in claim.associated_citation_ids:
                if cit_id in cit_by_id:
                    c_item = cit_by_id[cit_id]
                    ev = chunk_by_id.get(c_item.chunk_id)
                    if ev:
                        ind_score, ind_v = self._evaluate_support(
                            claim_text=claim.claim_text,
                            evidence_text=ev.text,
                        )
                        # In a multi-citation claim verified as a whole,
                        # any chunk that contributes entities or substantive overlap is verified
                        is_v = ind_v
                        eff_score = ind_score
                        if not is_v and is_claim_supported and len(claim.associated_citation_ids) > 1:
                            claim_ents = AcademicEntityExtractor.extract_entities(claim.claim_text)
                            ev_ents = AcademicEntityExtractor.extract_entities(ev.text)
                            c_norms = {e.normalized_entity for e in claim_ents}
                            e_norms = {e.normalized_entity for e in ev_ents}
                            shared_tokens = (
                                self._extract_substantive_tokens(claim.claim_text)
                                & self._extract_substantive_tokens(ev.text)
                            )
                            if (c_norms & e_norms) or len(shared_tokens) >= 2:
                                is_v = True
                                eff_score = claim_support_score

                        # Keep highest score if cited by multiple claims
                        prev = audited_citations.get(cit_id)
                        if prev is None or (eff_score > (prev.support_score or 0.0)):
                            audited_citations[cit_id] = c_item.model_copy(
                                update={
                                    "support_score": round(eff_score, 4),
                                    "is_verified": is_v,
                                }
                            )

            if is_claim_supported:
                audited_claims.append(
                    claim.model_copy(
                        update={
                            "is_supported": True,
                            "support_score": round(claim_support_score, 4),
                        }
                    )
                )
            else:
                audited_claims.append(
                    claim.model_copy(
                        update={
                            "is_supported": False,
                            "support_score": round(claim_support_score, 4),
                        }
                    )
                )
                unsupported_claims.append(claim.claim_text)

        # Build final list of audited citations (ensuring any citations not tied to claims are retained)
        final_citations: list[CitationItem] = []
        unverified_citations: list[str] = []

        for cit in citations:
            if cit.citation_id in audited_citations:
                updated_cit = audited_citations[cit.citation_id]
            else:
                updated_cit = cit.model_copy(update={"is_verified": False, "support_score": 0.0})

            final_citations.append(updated_cit)
            if not updated_cit.is_verified:
                unverified_citations.append(updated_cit.citation_id)

        # Operational metrics computation
        total_citations = len(final_citations)
        verified_citations_count = sum(1 for c in final_citations if c.is_verified)
        citation_precision = (
            round(verified_citations_count / total_citations, 4) if total_citations > 0 else 1.0
        )

        total_claims = len(audited_claims)
        supported_claims_count = sum(1 for c in audited_claims if c.is_supported)
        citation_recall = (
            round(supported_claims_count / total_claims, 4) if total_claims > 0 else 1.0
        )

        if audited_claims:
            overall_support = round(
                sum(c.support_score for c in audited_claims) / len(audited_claims), 4
            )
        else:
            overall_support = 1.0

        is_fully_supported = (
            len(unsupported_claims) == 0
            and len(unverified_citations) == 0
            and citation_recall >= 1.0
            and citation_precision >= 1.0
        )

        latency_ms = round((time.perf_counter() - t_0) * 1000.0, 2)

        return CitationVerificationResult(
            is_fully_supported=is_fully_supported,
            overall_support_score=overall_support,
            citation_precision=citation_precision,
            citation_recall=citation_recall,
            claims=audited_claims,
            citations=final_citations,
            unsupported_claims=unsupported_claims,
            unverified_citations=unverified_citations,
            verification_latency_ms=latency_ms,
        )

    def _evaluate_support(self, claim_text: str, evidence_text: str) -> tuple[float, bool]:
        """Evaluate deterministic support of claim against evidence text.

        Returns:
            (support_score, is_verified) in [0.0, 1.0] and boolean verification status.
        """
        if not claim_text.strip() or not evidence_text.strip():
            return 0.0, False

        # 1. Academic Entities Containment
        claim_ents = AcademicEntityExtractor.extract_entities(claim_text)
        ev_ents = AcademicEntityExtractor.extract_entities(evidence_text)

        ev_norms = {e.normalized_entity for e in ev_ents}
        claim_norms = {e.normalized_entity for e in claim_ents}

        entity_score = 1.0
        if claim_norms:
            contained_count = sum(1 for norm in claim_norms if norm in ev_norms)
            entity_score = contained_count / len(claim_norms)
            if self.require_exact_entities and entity_score < 1.0:
                # If claim asserts a specific course code, regulation, or date not in evidence,
                # claim cannot be verified by this evidence chunk
                return 0.0, False

        # 2. Exact Numbers / Percentages Precision (e.g., 75%, 15, 2026)
        claim_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", claim_text))
        ev_nums = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", evidence_text))

        num_score = 1.0
        if claim_nums:
            contained_nums = claim_nums & ev_nums
            num_score = len(contained_nums) / len(claim_nums)
            if num_score < 1.0:
                # Missing numeric figures directly penalize support
                return 0.0, False

        # 3. Substantive Token Overlap
        claim_tokens = self._extract_substantive_tokens(claim_text)
        ev_tokens = self._extract_substantive_tokens(evidence_text)

        if not claim_tokens:
            token_overlap = 1.0
        else:
            token_overlap = len(claim_tokens & ev_tokens) / len(claim_tokens)

        # 4. Subject-Predicate Co-occurrence check
        # Ensures that if claim contains a subject and a predicate (e.g. course code + 'mid examination'),
        # the evidence contains the predicate words as well.
        predicate_penalty = 1.0
        if "exam" in claim_text.lower() and "exam" not in evidence_text.lower():
            predicate_penalty = 0.0
        elif "attendance" in claim_text.lower() and "attendance" not in evidence_text.lower():
            predicate_penalty = 0.0

        # Weighted formula: 40% entity containment + 40% token overlap + 20% number precision
        support_score = (0.40 * entity_score + 0.40 * token_overlap + 0.20 * num_score) * predicate_penalty
        support_score = min(1.0, max(0.0, support_score))

        is_verified = support_score >= self.min_support_score
        return round(support_score, 4), is_verified

    def _extract_substantive_tokens(self, text: str) -> set[str]:
        """Extract substantive non-stopword tokens."""
        raw_words = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?", text.lower())
        return {w for w in raw_words if len(w) >= 2 and w not in self.STOPWORDS}
