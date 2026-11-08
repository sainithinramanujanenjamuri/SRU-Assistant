"""Weighted score combination for dense and lexical retrieval candidates."""

from collections.abc import Sequence
from typing import Any

from retrieval.models import HybridSearchResult, LexicalSearchResult, VectorSearchResult


class WeightedScoreFusion:
    """Combines normalized dense and lexical scores using convex linear weighting.

    Formula:
        fused_score(d) = alpha * dense_score(d) + (1 - alpha) * lexical_score(d)

    Where:
        - alpha is the weight assigned to dense retrieval (0.0 <= alpha <= 1.0)
        - dense_score(d) is the min-max normalized cosine score in [0.0, 1.0]
        - lexical_score(d) is the min-max normalized BM25 score in [0.0, 1.0]

    IMPORTANT: Dense normalized cosine and BM25 scores are not calibrated to the
    same empirical distribution. Setting alpha=0.5 is an initial heuristic and
    must not be presented as an optimal or calibrated relevance bound.
    Formal parameter calibration belongs to Phase 9.
    """

    def __init__(self, alpha: float = 0.5):
        if not (0.0 <= alpha <= 1.0):
            raise ValueError(f"Fusion weight alpha must be between 0.0 and 1.0, got {alpha}")
        self.alpha = alpha

    def fuse(
        self,
        dense_results: Sequence[VectorSearchResult],
        lexical_results: Sequence[LexicalSearchResult],
        top_k: int = 5,
    ) -> list[HybridSearchResult]:
        """Combine dense and lexical results using weighted score fusion.

        Args:
            dense_results: Dense search results with normalized_score in [0.0, 1.0].
            lexical_results: Lexical search results with normalized_score in [0.0, 1.0].
            top_k: Number of highest-scoring candidates to return.

        Returns:
            Ranked list of HybridSearchResult objects sorted by fused_score DESC, chunk_id ASC.
        """
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        candidate_map: dict[str, dict[str, Any]] = {}

        # 1. Process dense candidates
        for rank, res in enumerate(dense_results, start=1):
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
            }

        # 2. Process lexical candidates
        for rank, res in enumerate(lexical_results, start=1):
            if res.chunk_id in candidate_map:
                candidate_map[res.chunk_id]["lexical_rank"] = rank
                candidate_map[res.chunk_id]["lexical_score"] = res.normalized_score
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
                }

        if not candidate_map:
            return []

        # 3. Calculate convex combination
        # Missing modality score defaults to 0.0
        for item in candidate_map.values():
            d_score = item["dense_score"] if item["dense_score"] is not None else 0.0
            l_score = item["lexical_score"] if item["lexical_score"] is not None else 0.0
            item["fused_score"] = round(self.alpha * d_score + (1.0 - self.alpha) * l_score, 6)

        # 4. Deterministic sorting: fused_score DESC, chunk_id ASC
        sorted_items = sorted(
            candidate_map.values(),
            key=lambda item: (-item["fused_score"], item["chunk_id"]),
        )

        top_items = sorted_items[:top_k]

        fused_results: list[HybridSearchResult] = []
        for item in top_items:
            fused_score = item["fused_score"]
            fused_results.append(
                HybridSearchResult(
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    text=item["text"],
                    fused_score=fused_score,
                    normalized_fused_score=fused_score,  # already in [0.0, 1.0] by convex combination
                    dense_score=item["dense_score"],
                    dense_rank=item["dense_rank"],
                    lexical_score=item["lexical_score"],
                    lexical_rank=item["lexical_rank"],
                    fusion_method="weighted",
                    metadata=item["metadata"],
                    provenance=item["provenance"],
                )
            )

        return fused_results
