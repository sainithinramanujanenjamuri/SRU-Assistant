"""Neural cross-encoder adapter using sentence-transformers."""

from collections.abc import Sequence
from typing import Any

from retrieval.models import RerankerUnavailableError, RerankResult
from retrieval.reranking.base import BaseReranker


class TransformerCrossEncoderReranker(BaseReranker):
    """Neural cross-encoder adapter using sentence-transformers.

    Requires the 'sentence-transformers' package and a pre-trained cross-encoder model
    (e.g., 'cross-encoder/ms-marco-MiniLM-L-6-v2' or 'BAAI/bge-reranker-base').

    If sentence-transformers is not installed or the model cannot be loaded,
    raises RerankerUnavailableError explicitly without silent fallback.
    """

    reranker_name: str = "transformer"
    reranker_provider: str = "sentence-transformers"

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.reranker_model = model_name
        self._model = None

    def _get_model(self) -> Any:
        """Lazily load the cross-encoder model with explicit error handling."""
        if self._model is not None:
            return self._model

        try:
            from sentence_transformers import CrossEncoder
        except ImportError as e:
            raise RerankerUnavailableError(
                f"sentence-transformers package is not installed in this environment: {e}. "
                "Use 'pip install sentence-transformers' or configure reranker_type='deterministic'."
            ) from e

        try:
            self._model = CrossEncoder(self.reranker_model)
            return self._model
        except Exception as e:
            raise RerankerUnavailableError(
                f"Failed to load neural cross-encoder model '{self.reranker_model}': {e}"
            ) from e

    def rerank(
        self,
        query: str,
        candidates: Sequence[Any],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Re-rank candidate evidence using neural cross-encoder joint scoring."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        if not candidates:
            return []

        model = self._get_model()

        pairs = [(query, getattr(c, "text", "")) for c in candidates]
        try:
            raw_scores = model.predict(pairs)
        except Exception as e:
            raise RerankerUnavailableError(f"Cross-encoder inference failed: {e}") from e

        # Normalize scores to [0.0, 1.0] using sigmoid: 1 / (1 + exp(-s))
        import math

        scored: list[dict[str, Any]] = []
        for rank, (cand, s) in enumerate(zip(candidates, raw_scores), start=1):
            score_val = float(s)
            # Sigmoid transformation
            norm_s = 1.0 / (1.0 + math.exp(-score_val))
            norm_s = max(0.0, min(1.0, round(norm_s, 6)))

            scored.append({
                "cand": cand,
                "chunk_id": getattr(cand, "chunk_id", str(rank)),
                "document_id": getattr(cand, "document_id", "unknown_doc"),
                "text": getattr(cand, "text", ""),
                "initial_rank": rank,
                "initial_score": getattr(
                    cand, "normalized_fused_score",
                    getattr(cand, "normalized_score", getattr(cand, "score", 0.0))
                ),
                "rerank_score": norm_s,
                "metadata": getattr(cand, "metadata", {}) or {},
                "provenance": getattr(cand, "provenance", {}) or {},
            })

        # Deterministic sort: rerank_score DESC, chunk_id ASC
        scored.sort(key=lambda x: (-x["rerank_score"], str(x["chunk_id"])))

        results: list[RerankResult] = []
        for rerank_rank, item in enumerate(scored[:top_k], start=1):
            cand = item["cand"]
            init_rank = item["initial_rank"]
            results.append(
                RerankResult(
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    text=item["text"],
                    rerank_score=item["rerank_score"],
                    initial_score=item["initial_score"],
                    initial_rank=init_rank,
                    rerank_rank=rerank_rank,
                    rank_delta=init_rank - rerank_rank,
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
            )

        return results
