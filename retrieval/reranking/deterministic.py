"""Deterministic cross-feature relevance scoring baseline for candidate re-ranking."""
from __future__ import annotations


import re
from collections.abc import Sequence
from typing import Any

from retrieval.lexical.tokenizer import AcademicLexicalTokenizer
from retrieval.models import RerankResult
from retrieval.reranking.base import BaseReranker


class DeterministicCrossFeatureReranker(BaseReranker):
    """Deterministic cross-feature relevance scoring baseline.


    IMPORTANT ARCHITECTURAL NOTE:
    This class is NOT a trained neural cross-encoder. It does NOT possess deep semantic
    understanding equivalent to a fine-tuned transformer.

    Instead, it evaluates joint Query + Passage lexical and structural interaction features:
    - Query token coverage (fraction of distinct query tokens present in the passage).
    - Exact institutional entity match bonuses (course codes, regulations, dates, exam terms).
    - Token proximity and span density (rewarding tight clusters of query terms).
    - Heading and hierarchical section alignment.

    It serves as a fast, reproducible, offline-capable baseline for CI, ablation experiments,
    and comparative evaluations against neural models.
    """

    reranker_name: str = "deterministic"
    reranker_provider: str = "deterministic"
    reranker_model: str = "deterministic-cross-feature-v1"

    COURSE_CODE_PATTERN = re.compile(r"\b(?:2[0-9])?[A-Z]{2,4}\d{3}[A-Z]?\b", re.IGNORECASE)
    REGULATION_PATTERN = re.compile(r"\b[Rr](\d{2})\b")
    DATE_PATTERN = re.compile(
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        re.IGNORECASE,
    )
    EXAM_TERMS = [
        "First Mid Examinations",
        "Second Mid Examinations",
        "Mid-Semester Examination I",
        "Mid-Semester Examination II",
        "End Semester Examinations",
        "Mid Examinations",
        "Mid Examination",
    ]

    def __init__(self, tokenizer: AcademicLexicalTokenizer | None = None):
        self.tokenizer = tokenizer or AcademicLexicalTokenizer()

    def rerank(
        self,
        query: str,
        candidates: Sequence[Any],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Re-rank candidates using joint query-passage cross-features.

        Args:
            query: User query string.
            candidates: Sequence of candidate search results.
            top_k: Maximum number of ranked results to return.

        Returns:
            List of RerankResult objects ordered deterministically (rerank_score DESC, chunk_id ASC).
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        if not candidates:
            return []

        query_tokens = set(self.tokenizer.tokenize(query))
        query_text_lower = query.lower()

        # Extract entities from query for exact cross-matching
        query_course_codes = {
            m.group(0).upper()
            for m in self.COURSE_CODE_PATTERN.finditer(query)
            if not re.match(r"^R\d{2}$", m.group(0), re.IGNORECASE)
        }
        query_regulations = {f"R{m.group(1)}" for m in self.REGULATION_PATTERN.finditer(query)}
        query_dates = {m.group(0).lower() for m in self.DATE_PATTERN.finditer(query)}
        query_exam_terms = {t.lower() for t in self.EXAM_TERMS if t.lower() in query_text_lower}

        scored_candidates: list[dict[str, Any]] = []

        for initial_rank, cand in enumerate(candidates, start=1):
            text = getattr(cand, "text", "")
            chunk_tokens = self.tokenizer.tokenize(text)
            chunk_token_set = set(chunk_tokens)
            meta = getattr(cand, "metadata", {}) or {}
            prov = getattr(cand, "provenance", {}) or {}
            chunk_id = getattr(cand, "chunk_id", str(initial_rank))
            doc_id = getattr(cand, "document_id", "unknown_doc")

            # Pre-reranking candidate score
            initial_score = getattr(
                cand, "normalized_fused_score",
                getattr(cand, "normalized_score", getattr(cand, "score", 0.0))
            )

            # Feature 1: Query token coverage [0.0, 1.0]
            if query_tokens:
                matching_tokens = query_tokens.intersection(chunk_token_set)
                coverage = len(matching_tokens) / len(query_tokens)
            else:
                matching_tokens = set()
                coverage = 0.0

            # Feature 2: Exact academic entity matching bonuses
            entity_bonus = 0.0

            # Course code match
            if query_course_codes:
                text_upper = text.upper()
                chunk_codes = {c.upper() for c in meta.get("chunk_course_codes", [])}
                if any(code in text_upper or code in chunk_codes for code in query_course_codes):
                    entity_bonus += 0.60

            # Regulation match
            if query_regulations:
                text_reg = {f"R{m.group(1)}" for m in self.REGULATION_PATTERN.finditer(text)}
                doc_reg = {str(r).upper() for r in meta.get("regulations", []) + meta.get("chunk_regulations", [])}
                if query_regulations.intersection(text_reg | doc_reg):
                    entity_bonus += 0.50

            # Date match
            if query_dates:
                text_dates = {m.group(0).lower() for m in self.DATE_PATTERN.finditer(text)}
                doc_dates = {str(d).lower() for d in meta.get("chunk_dates", [])}
                if query_dates.intersection(text_dates | doc_dates):
                    entity_bonus += 0.55

            # Examination term match
            if query_exam_terms:
                text_lower = text.lower()
                doc_exams = {str(e).lower() for e in meta.get("chunk_examinations", [])}
                if any(term in text_lower or term in doc_exams for term in query_exam_terms):
                    entity_bonus += 0.45

            # Feature 3: Token proximity and span density
            proximity_density = 0.0
            if len(matching_tokens) >= 2 and len(chunk_tokens) > 1:
                # Find positions of matching tokens in the token list
                matching_indices = [
                    i for i, tok in enumerate(chunk_tokens) if tok in matching_tokens
                ]
                if matching_indices:
                    span = max(matching_indices) - min(matching_indices) + 1
                    # Density: ratio of matching tokens to total span
                    proximity_density = min(0.15, round(len(matching_tokens) / max(1, span), 4))

            # Feature 4: Heading alignment
            heading_bonus = 0.0
            sec_path = str(meta.get("section_path", "")).lower()
            hierarchy = [str(h).lower() for h in meta.get("heading_hierarchy", [])]
            heading_text = sec_path + " " + " ".join(hierarchy)
            if any(q_tok in heading_text for q_tok in query_tokens if len(q_tok) > 2):
                heading_bonus = 0.10

            # Cross-score combination
            # 35% initial candidate retrieval score + 65% joint cross-feature interaction
            cross_feature_score = (
                0.40 * coverage +
                0.35 * min(1.0, entity_bonus) +
                0.15 * proximity_density +
                0.10 * heading_bonus
            )

            final_score = round(
                max(0.0, min(1.0, 0.35 * initial_score + 0.65 * cross_feature_score)),
                6,
            )

            scored_candidates.append({
                "cand": cand,
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "text": text,
                "initial_rank": initial_rank,
                "initial_score": initial_score,
                "rerank_score": final_score,
                "metadata": meta,
                "provenance": prov,
            })

        # Deterministic sort: rerank_score DESC, chunk_id ASC
        scored_candidates.sort(
            key=lambda x: (-x["rerank_score"], str(x["chunk_id"]))
        )

        # Slice to top_k and assign final rerank_rank
        results: list[RerankResult] = []
        for rerank_rank, item in enumerate(scored_candidates[:top_k], start=1):
            cand = item["cand"]
            init_rank = item["initial_rank"]
            rank_delta = init_rank - rerank_rank  # Positive = moved up, Negative = moved down

            res = RerankResult(
                chunk_id=item["chunk_id"],
                document_id=item["document_id"],
                text=item["text"],
                rerank_score=item["rerank_score"],
                initial_score=item["initial_score"],
                initial_rank=init_rank,
                rerank_rank=rerank_rank,
                rank_delta=rank_delta,
                reranker_name=self.reranker_name,
                reranker_provider=self.reranker_provider,
                reranker_model=self.reranker_model,
                dense_score=getattr(cand, "dense_score", None),
                dense_rank=getattr(cand, "dense_rank", None),
                lexical_score=getattr(cand, "lexical_score", None),
                lexical_rank=getattr(cand, "lexical_rank", None),
                initial_hybrid_rank=getattr(cand, "initial_hybrid_rank", init_rank),
                original_retrieval_mode=getattr(cand, "fusion_method", "hybrid"),
                metadata=item["metadata"],
                provenance=item["provenance"],
            )
            results.append(res)

        return results


# Alias for backward/spec compatibility
DeterministicCrossEncoderReranker = DeterministicCrossFeatureReranker
