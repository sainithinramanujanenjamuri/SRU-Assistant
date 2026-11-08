"""Base protocol for re-ranking components in SRU Assistant."""

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from retrieval.models import RerankResult


@runtime_checkable
class BaseReranker(Protocol):
    """Protocol defining the standard interface for candidate re-rankers.

    Implemented by:
    - DeterministicCrossFeatureReranker (deterministic cross-scoring baseline)
    - TransformerCrossEncoderReranker (neural sentence-transformers adapter)
    - OllamaCrossEncoderReranker (local LLM cross-scorer)
    - PassthroughReranker (identity baseline for ablation experiments)
    """

    reranker_name: str
    reranker_provider: str
    reranker_model: str

    def rerank(
        self,
        query: str,
        candidates: Sequence[Any],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Re-rank candidate evidence chunks against the query.

        Args:
            query: Query string.
            candidates: Sequence of retrieved candidate objects.
            top_k: Number of highest-ranked chunks to return.

        Returns:
            Ranked list of RerankResult instances.
        """
        ...
