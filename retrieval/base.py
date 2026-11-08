"""Base protocol for all retrieval components in SRU Assistant."""
from __future__ import annotations


from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class BaseRetriever(Protocol):
    """Protocol defining the standard interface for all retrievers.


    Implemented by:
    - VectorRetriever (dense semantic search)
    - BM25Retriever (sparse lexical search)
    - HybridRetriever (fused multi-channel search)
    """

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> Sequence[Any]:
        """Execute retrieval against the indexed corpus.

        Args:
            query: Natural language or keyword query string.
            top_k: Number of highest-ranked chunks to return.
            filters: Optional metadata pre-filtering constraints.

        Returns:
            Ranked sequence of search result objects (VectorSearchResult,
            LexicalSearchResult, or HybridSearchResult).
        """
        ...
