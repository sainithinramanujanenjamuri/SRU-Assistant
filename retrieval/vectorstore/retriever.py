"""Semantic vector retriever querying the persistent vector database."""
from __future__ import annotations


from typing import Any

from retrieval.base import BaseRetriever
from retrieval.embeddings.base import BaseEmbeddingModel
from retrieval.models import VectorSearchResult
from retrieval.vectorstore.base import BaseVectorStore


class VectorRetriever(BaseRetriever):
    """Semantic vector retriever executing natural-language similarity queries against a vector store.


    Enforces manifest compatibility, query validation, and metadata preservation for downstream RAG.
    """

    retrieval_mode: str = "dense"

    def __init__(self, embedding_model: BaseEmbeddingModel, vector_store: BaseVectorStore):
        self.model = embedding_model
        self.store = vector_store

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Execute semantic search against the vector index.

        Args:
            query: Natural language query string (cannot be empty).
            top_k: Number of highest-similarity chunks to return (must be > 0).
            filters: Optional dictionary of metadata criteria (e.g. {"department": "CSE"}).

        Returns:
            List of VectorSearchResult objects sorted by similarity descending.

        Raises:
            ValueError: If query is blank or top_k <= 0.
            IndexCompatibilityError: If query model is incompatible with index manifest.
            EmbeddingError: If query embedding fails.
            VectorStoreError: If database read fails.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        # Validate manifest compatibility if an index manifest exists
        self.store.validate_manifest_compatibility(
            self.model.provider_name,
            self.model.model_name,
            self.model.dimension,
        )

        # Check if the index contains records
        if self.store.count() == 0:
            return []

        # Generate query embedding
        query_vector = self.model.embed_text(query.strip())

        # Perform vector similarity search
        return self.store.search(query_vector=query_vector, top_k=top_k, filters=filters)
