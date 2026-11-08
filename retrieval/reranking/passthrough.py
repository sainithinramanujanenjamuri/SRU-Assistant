"""Passthrough (identity) candidate re-ranker for baseline ablation experiments."""

from collections.abc import Sequence
from typing import Any

from retrieval.models import RerankResult
from retrieval.reranking.base import BaseReranker


class PassthroughReranker(BaseReranker):
    """Identity re-ranker that preserves input candidate order and scores without modification.

    Used specifically for ablation studies comparing enhanced retrieval pipelines
    with and without the re-ranking stage.
    """

    reranker_name: str = "passthrough"
    reranker_provider: str = "passthrough"
    reranker_model: str = "identity"

    def rerank(
        self,
        query: str,
        candidates: Sequence[Any],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Pass through candidates up to top_k preserving initial scores and ranks."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        if not candidates:
            return []

        results: list[RerankResult] = []
        for rank, cand in enumerate(candidates[:top_k], start=1):
            init_score = getattr(
                cand, "normalized_fused_score",
                getattr(cand, "normalized_score", getattr(cand, "score", 0.0))
            )
            results.append(
                RerankResult(
                    chunk_id=getattr(cand, "chunk_id", str(rank)),
                    document_id=getattr(cand, "document_id", "unknown_doc"),
                    text=getattr(cand, "text", ""),
                    rerank_score=init_score,
                    initial_score=init_score,
                    initial_rank=rank,
                    rerank_rank=rank,
                    rank_delta=0,
                    reranker_name=self.reranker_name,
                    reranker_provider=self.reranker_provider,
                    reranker_model=self.reranker_model,
                    dense_score=getattr(cand, "dense_score", None),
                    dense_rank=getattr(cand, "dense_rank", None),
                    lexical_score=getattr(cand, "lexical_score", None),
                    lexical_rank=getattr(cand, "lexical_rank", None),
                    initial_hybrid_rank=getattr(cand, "initial_hybrid_rank", rank),
                    original_retrieval_mode=getattr(cand, "fusion_method", "hybrid"),
                    metadata=getattr(cand, "metadata", {}) or {},
                    provenance=getattr(cand, "provenance", {}) or {},
                )
            )

        return results
