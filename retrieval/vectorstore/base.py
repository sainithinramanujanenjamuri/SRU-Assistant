"""Abstract base class for vector store backends."""
from __future__ import annotations


from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import Any

from retrieval.models import IndexManifest, VectorRecord, VectorSearchResult


class BaseVectorStore(ABC):
    """Abstract interface defining the contract for persistent vector databases."""


    @abstractmethod
    def add_records(self, records: Sequence[VectorRecord]) -> int:
        """Insert or replace vector records in the store.

        Returns the number of records successfully written.
        """
        pass

    @abstractmethod
    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Perform similarity search using query vector and optional metadata filters.

        Args:
            query_vector: Unit-normalized float vector.
            top_k: Maximum number of results to return (must be > 0).
            filters: Dictionary of metadata filter criteria (e.g. department="CSE").

        Returns:
            Ranked list of VectorSearchResult objects.
        """
        pass

    @abstractmethod
    def get_record(self, chunk_id: str) -> VectorRecord | None:
        """Retrieve a vector record by chunk ID."""
        pass

    @abstractmethod
    def delete_records(self, chunk_ids: Sequence[str]) -> int:
        """Delete records with the given chunk IDs. Returns number of records deleted."""
        pass

    @abstractmethod
    def count(self) -> int:
        """Return the total number of records currently stored."""
        pass

    @abstractmethod
    def clear(self) -> None:
        """Remove all records and reset the vector store."""
        pass

    @abstractmethod
    def save_manifest(self, manifest: IndexManifest) -> None:
        """Persist the index manifest metadata."""
        pass

    @abstractmethod
    def get_manifest(self) -> IndexManifest | None:
        """Retrieve the persisted index manifest, if present."""
        pass

    def validate_manifest_compatibility(self, provider: str, model: str, dimension: int) -> None:
        """Check if an embedding model is compatible with the stored index manifest.

        Raises IndexCompatibilityError if incompatible.
        """
        manifest = self.get_manifest()
        if manifest is not None and manifest.total_vectors > 0:
            is_compat, reason = manifest.is_compatible_with(provider, model, dimension)
            if not is_compat:
                from retrieval.models import IndexCompatibilityError
                raise IndexCompatibilityError(reason)
