"""Reciprocal Rank Fusion (RRF) algorithm for multi-channel retrieval."""

from collections.abc import Sequence
from typing import Any

from retrieval.models import HybridSearchResult, LexicalSearchResult, VectorSearchResult


class ReciprocalRankFusion:
    """Combines ranked candidate lists using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF(d) = sum(w_m / (k + rank_m(d))) for m in {dense, lexical}

    Where:
        - k is a smoothing constant (standard default: 60)
        - rank_m(d) is the 1-indexed rank of candidate d in modality m
        - w_m is the weight assigned to modality m

    IMPORTANT: RRF produces a rank-order aggregation score, NOT a calibrated
    probability, likelihood, or semantic similarity value.
    """

    def __init__(
        self,
        k: int = 60,
        dense_weight: float = 1.0,
        lexical_weight: float = 1.0,
    ):
        if k < 0:
            raise ValueError(f"RRF constant k must be non-negative, got {k}")
        if dense_weight < 0.0 or lexical_weight < 0.0:
            raise ValueError("Modality weights must be non-negative")
        if dense_weight == 0.0 and lexical_weight == 0.0:
            raise ValueError("At least one modality weight must be strictly positive")

        self.k = k
        self.dense_weight = dense_weight
        self.lexical_weight = lexical_weight

        # Theoretical maximum score achievable by a candidate ranked #1 in both channels
        self.max_theoretical_rrf = (self.dense_weight / (self.k + 1)) + (self.lexical_weight / (self.k + 1))

    def fuse(
        self,
        dense_results: Sequence[VectorSearchResult],
        lexical_results: Sequence[LexicalSearchResult],
        top_k: int = 5,
    ) -> list[HybridSearchResult]:
        """Fuse dense and lexical candidate lists into a unified ranked list.

        Args:
            dense_results: Candidates retrieved from vector store, sorted by similarity.
            lexical_results: Candidates retrieved from BM25, sorted by BM25 score.
            top_k: Maximum number of unified candidates to return.

        Returns:
            List of HybridSearchResult objects sorted by fused_score DESC, chunk_id ASC.
        """
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        candidate_map: dict[str, dict[str, Any]] = {}

        # 1. Process dense candidates
        for rank, res in enumerate(dense_results, start=1):
            rrf_contrib = self.dense_weight / (self.k + rank)
            candidate_map[res.chunk_id] = {
                "chunk_id": res.chunk_id,
                "document_id": res.document_id,
                "text": res.text,
                "metadata": res.metadata,
                "provenance": res.provenance,
                "dense_rank": rank,
                "dense_score": res.normalized_score,
                "lexical_rank": None,
                "lexical_score": None,
                "raw_rrf": rrf_contrib,
            }

        # 2. Process lexical candidates
        for rank, res in enumerate(lexical_results, start=1):
            rrf_contrib = self.lexical_weight / (self.k + rank)
            if res.chunk_id in candidate_map:
                candidate_map[res.chunk_id]["lexical_rank"] = rank
                candidate_map[res.chunk_id]["lexical_score"] = res.normalized_score
                candidate_map[res.chunk_id]["raw_rrf"] += rrf_contrib
            else:
                candidate_map[res.chunk_id] = {
                    "chunk_id": res.chunk_id,
                    "document_id": res.document_id,
                    "text": res.text,
                    "metadata": res.metadata,
                    "provenance": res.provenance,
                    "dense_rank": None,
                    "dense_score": None,
                    "lexical_rank": rank,
                    "lexical_score": res.normalized_score,
                    "raw_rrf": rrf_contrib,
                }

        if not candidate_map:
            return []

        # 3. Deterministic sorting: fused_score DESC, chunk_id ASC
        sorted_items = sorted(
            candidate_map.values(),
            key=lambda item: (-item["raw_rrf"], item["chunk_id"]),
        )

        top_items = sorted_items[:top_k]

        fused_results: list[HybridSearchResult] = []
        for item in top_items:
            raw_rrf = item["raw_rrf"]
            # Normalized score in [0.0, 1.0] by dividing by theoretical max
            norm_score = (
                round(min(1.0, raw_rrf / self.max_theoretical_rrf), 6)
                if self.max_theoretical_rrf > 0
                else 0.0
            )

            fused_results.append(
                HybridSearchResult(
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    text=item["text"],
                    fused_score=round(raw_rrf, 6),
                    normalized_fused_score=norm_score,
                    dense_score=item["dense_score"],
                    dense_rank=item["dense_rank"],
                    lexical_score=item["lexical_score"],
                    lexical_rank=item["lexical_rank"],
                    fusion_method="rrf",
                    metadata=item["metadata"],
                    provenance=item["provenance"],
                )
            )

        return fused_results
