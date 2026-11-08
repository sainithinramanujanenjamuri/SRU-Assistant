"""Abstract base class for all embedding models."""
from __future__ import annotations


import math
from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np


class BaseEmbeddingModel(ABC):
    """Abstract interface that all embedding providers (FastHash, Ollama, etc.) must implement."""


    @property
    @abstractmethod
    def provider_name(self) -> str:
        """Name of the embedding provider (e.g. 'fasthash', 'ollama')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Identifier of the model used (e.g. 'fasthash-384', 'nomic-embed-text')."""
        pass

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Output dimensionality of embedding vectors."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> list[float]:
        """Generate a unit-normalized embedding vector for a single text input.

        Raises:
            ValueError: If text is empty or contains only whitespace.
            EmbeddingError: If the embedding model fails.
        """
        pass

    @abstractmethod
    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate unit-normalized embedding vectors for a sequence of text inputs.

        Raises:
            ValueError: If texts sequence is empty or any element is blank.
            EmbeddingError: If the embedding model fails.
        """
        pass

    @staticmethod
    def normalize_vector(vector: Sequence[float] | np.ndarray) -> list[float]:
        """Normalize a vector to unit length (L2 norm = 1.0).

        If the vector is all zeros or norm is negligible, returns the original vector.
        """
        arr = np.asarray(vector, dtype=np.float32)
        norm = float(np.linalg.norm(arr))
        if norm > 1e-12 and not math.isnan(norm):
            arr = arr / norm
        return [float(x) for x in arr]

    @staticmethod
    def validate_text(text: str) -> str:
        """Validate and return cleaned input text, rejecting empty or whitespace-only strings."""
        if not isinstance(text, str):
            raise ValueError(f"Expected string input for embedding, got {type(text).__name__}")
        cleaned = text.strip()
        if not cleaned:
            raise ValueError("Cannot embed empty or whitespace-only text")
        return cleaned
