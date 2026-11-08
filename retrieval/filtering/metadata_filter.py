"""Institutional metadata filtering with null-safe global document preservation."""
from __future__ import annotations


from collections.abc import Sequence
from typing import Any

from app.config.settings import get_settings
from retrieval.models import (
    FilterError,
    HybridSearchResult,
    LexicalSearchResult,
    VectorSearchResult,
)


class MetadataFilter:
    """Evaluates and filters candidate search results using institutional metadata constraints.


    Design Principles:
    1. Null-Safe Global Evidence: Documents with field == None are explicitly university-wide/global
       (e.g., academic calendar) and must never be pruned when filtering by department or program.
    2. Unknown vs Global Distinction: Explicit None means global; missing key means unknown applicability.
    3. Soft vs Hard Modes:
       - Soft mode: Applies deterministic bounded boost/penalty to candidate score.
       - Hard mode: Prunes ineligible candidates while preserving global evidence.
    4. Normalization: Normalizes known academic aliases (e.g. 'CSE' <-> 'Computer Science and Engineering')
       case-insensitively.
    """

    # Known canonical aliases
    ALIASES = {
        "department": {
            "cse": "computer science and engineering",
            "computer science": "computer science and engineering",
            "computer science and engineering": "computer science and engineering",
            "ece": "electronics and communication engineering",
            "electronics": "electronics and communication engineering",
            "electronics and communication": "electronics and communication engineering",
            "electronics and communication engineering": "electronics and communication engineering",
            "eee": "electrical and electronics engineering",
            "electrical": "electrical and electronics engineering",
            "mech": "mechanical engineering",
            "mechanical": "mechanical engineering",
            "mechanical engineering": "mechanical engineering",
            "civil": "civil engineering",
            "civil engineering": "civil engineering",
        },
        "program": {
            "b.tech": "b.tech",
            "btech": "b.tech",
            "b tech": "b.tech",
            "m.tech": "m.tech",
            "mtech": "m.tech",
            "m tech": "m.tech",
            "mba": "mba",
            "mca": "mca",
            "ph.d": "ph.d",
            "phd": "ph.d",
        },
        "semester": {
            "1": "semester i",
            "i": "semester i",
            "semester 1": "semester i",
            "semester i": "semester i",
            "2": "semester ii",
            "ii": "semester ii",
            "semester 2": "semester ii",
            "semester ii": "semester ii",
            "3": "semester iii",
            "iii": "semester iii",
            "semester 3": "semester iii",
            "semester iii": "semester iii",
            "4": "semester iv",
            "iv": "semester iv",
            "semester 4": "semester iv",
            "semester iv": "semester iv",
            "5": "semester v",
            "v": "semester v",
            "semester 5": "semester v",
            "semester v": "semester v",
            "6": "semester vi",
            "vi": "semester vi",
            "semester 6": "semester vi",
            "semester vi": "semester vi",
            "7": "semester vii",
            "vii": "semester vii",
            "semester 7": "semester vii",
            "semester vii": "semester vii",
            "8": "semester viii",
            "viii": "semester viii",
            "semester 8": "semester viii",
            "semester viii": "semester viii",
        },
    }

    def __init__(
        self,
        mode: str = "soft",
        boost: float | None = None,
        penalty: float | None = None,
        strict_completeness: bool = False,
    ):
        settings = get_settings()
        self.mode = (mode or settings.retrieval_filter_mode).lower()
        if self.mode not in ("soft", "hard"):
            raise FilterError(f"Invalid filter mode '{mode}'. Must be 'soft' or 'hard'.")

        self.boost = boost if boost is not None else settings.soft_filter_boost
        self.penalty = penalty if penalty is not None else settings.soft_filter_penalty
        self.strict_completeness = strict_completeness

    def filter_candidates(
        self,
        candidates: Sequence[Any],
        filters: dict[str, Any] | None = None,
        mode_override: str | None = None,
    ) -> list[Any]:
        """Apply metadata filtering to candidate list.

        Args:
            candidates: Sequence of VectorSearchResult, LexicalSearchResult, or HybridSearchResult.
            filters: Metadata constraints (e.g. {'department': 'CSE', 'semester': 'Semester VII'}).
            mode_override: Optional override for 'soft' or 'hard' filtering.

        Returns:
            Filtered and/or score-adjusted list of candidates.
        """
        if not candidates:
            return []

        if not filters:
            return list(candidates)

        active_mode = (mode_override or self.mode).lower()
        if active_mode == "hard":
            return self._apply_hard_filter(candidates, filters)
        elif active_mode == "soft":
            return self._apply_soft_filter(candidates, filters)
        else:
            raise FilterError(f"Invalid filter mode '{active_mode}'. Must be 'soft' or 'hard'.")

    def _normalize_val(self, field: str, val: Any) -> str | None:
        """Normalize a field value for robust alias comparison."""
        if val is None:
            return None
        s = str(val).strip().lower()
        if not s:
            return None
        alias_dict = self.ALIASES.get(field, {})
        return alias_dict.get(s, s)

    def _matches_field(self, field: str, constraint: Any, doc_meta: dict[str, Any]) -> tuple[bool, bool]:
        """Evaluate a single constraint against document metadata.

        Returns:
            (is_eligible, is_match):
            - is_eligible: True if eligible in hard mode (matches, or is global/unknown).
            - is_match: True if explicitly matches target constraint.
        """
        if field not in doc_meta:
            # Field missing from metadata -> Unknown applicability
            is_eligible = not self.strict_completeness
            return is_eligible, False

        doc_val = doc_meta[field]

        # Explicit None in document metadata -> University-wide / Global evidence
        if doc_val is None:
            return True, False  # Eligible (never pruned), but not a specific scoped match

        target_norm = self._normalize_val(field, constraint)

        # Handle list fields (e.g. regulations = ['R23'] or chunk_dates = [...])
        if isinstance(doc_val, (list, tuple, set)):
            doc_norms = [self._normalize_val(field, item) for item in doc_val if item is not None]
            is_match = target_norm in doc_norms
            return is_match, is_match

        doc_norm = self._normalize_val(field, doc_val)
        is_match = (doc_norm == target_norm)
        return is_match, is_match

    def _apply_hard_filter(
        self,
        candidates: Sequence[Any],
        filters: dict[str, Any],
    ) -> list[Any]:
        """Hard filtering: drops non-matching candidates while preserving global evidence."""
        surviving = []
        for cand in candidates:
            meta = getattr(cand, "metadata", {}) or {}
            eligible = True
            for field, constraint in filters.items():
                if constraint is None:
                    continue
                is_elig, _ = self._matches_field(field, constraint, meta)
                if not is_elig:
                    eligible = False
                    break
            if eligible:
                surviving.append(cand)
        return surviving

    def _apply_soft_filter(
        self,
        candidates: Sequence[Any],
        filters: dict[str, Any],
    ) -> list[Any]:
        """Soft filtering: applies deterministic score boost/penalty based on metadata match.

        Score formula:
            adjusted_score = clamp(base_score + delta, 0.0, 1.0)
            where:
                match: +boost (e.g. +0.15)
                global (field is None): 0.0 (no penalty)
                missing/unknown: 0.0 (neutral)
                non-global mismatch: -penalty (e.g. -0.15)
        """
        adjusted_candidates = []
        for cand in candidates:
            meta = getattr(cand, "metadata", {}) or {}
            delta = 0.0

            for field, constraint in filters.items():
                if constraint is None:
                    continue

                if field not in meta:
                    # Missing metadata -> neutral
                    continue

                doc_val = meta[field]
                if doc_val is None:
                    # Explicit global document -> neutral (no penalty)
                    continue

                _, is_match = self._matches_field(field, constraint, meta)
                if is_match:
                    delta += self.boost
                else:
                    delta -= self.penalty

            base_score = getattr(cand, "normalized_score", getattr(cand, "score", 0.0))
            new_score = max(0.0, min(1.0, round(base_score + delta, 6)))

            # Clone candidate with updated score
            adjusted_cand = self._clone_with_score(cand, new_score)
            adjusted_candidates.append(adjusted_cand)

        # Sort deterministically: score DESC, chunk_id ASC
        adjusted_candidates.sort(
            key=lambda c: (-getattr(c, "normalized_score", 0.0), str(getattr(c, "chunk_id", "")))
        )
        return adjusted_candidates

    @staticmethod
    def _clone_with_score(cand: Any, new_score: float) -> Any:
        """Create a shallow copy of search result with updated normalized score."""
        if isinstance(cand, HybridSearchResult):
            return HybridSearchResult(
                chunk_id=cand.chunk_id,
                document_id=cand.document_id,
                text=cand.text,
                fused_score=new_score,
                normalized_fused_score=new_score,
                dense_score=cand.dense_score,
                dense_rank=cand.dense_rank,
                lexical_score=cand.lexical_score,
                lexical_rank=cand.lexical_rank,
                fusion_method=cand.fusion_method,
                metadata=cand.metadata,
                provenance=cand.provenance,
            )
        elif isinstance(cand, VectorSearchResult):
            return VectorSearchResult(
                chunk_id=cand.chunk_id,
                document_id=cand.document_id,
                text=cand.text,
                cosine_similarity=cand.cosine_similarity,
                normalized_score=new_score,
                metadata=cand.metadata,
                provenance=cand.provenance,
            )
        elif isinstance(cand, LexicalSearchResult):
            return LexicalSearchResult(
                chunk_id=cand.chunk_id,
                document_id=cand.document_id,
                text=cand.text,
                bm25_score=cand.bm25_score,
                normalized_score=new_score,
                rank=cand.rank,
                metadata=cand.metadata,
                provenance=cand.provenance,
            )
        else:
            # Fallback for generic duck-typed result
            if hasattr(cand, "copy"):
                clone = cand.copy()
            else:
                import copy
                clone = copy.copy(cand)
            if hasattr(clone, "normalized_score"):
                clone.normalized_score = new_score
            return clone
