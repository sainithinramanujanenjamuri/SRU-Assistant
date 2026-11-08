"""Optional SentenceTransformers embedding model adapter."""

from collections.abc import Sequence
from typing import Any

from retrieval.embeddings.base import BaseEmbeddingModel
from retrieval.models import EmbeddingError


class SentenceTransformersEmbeddingModel(BaseEmbeddingModel):
    """Adapter for sentence-transformers models running locally via PyTorch."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2", dimension: int = 384):
        self._model_name = model_name
        self._dimension = dimension
        self._model: Any = None

    @property
    def provider_name(self) -> str:
        return "sentence_transformers"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    @classmethod
    def is_available(cls) -> tuple[bool, str]:
        """Check whether sentence-transformers package is installed."""
        try:
            import sentence_transformers  # noqa: F401
            return True, "Available"
        except ImportError:
            return False, "sentence-transformers package is not installed."

    def _get_model(self) -> Any:
        if self._model is None:
            available, msg = self.is_available()
            if not available:
                raise EmbeddingError(msg)
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self._model_name)
                # Read actual dimension from model if available
                dim = self._model.get_sentence_embedding_dimension()
                if dim is not None:
                    self._dimension = int(dim)
            except Exception as e:
                raise EmbeddingError(f"Failed to load sentence-transformers model '{self._model_name}': {e}") from e
        return self._model

    def embed_text(self, text: str) -> list[float]:
        cleaned = self.validate_text(text)
        model = self._get_model()
        vec = model.encode(cleaned, normalize_embeddings=True)
        return [float(x) for x in vec]

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        if not texts:
            return []
        cleaned_texts = [self.validate_text(t) for t in texts]
        model = self._get_model()
        vectors = model.encode(cleaned_texts, normalize_embeddings=True)
        return [[float(x) for x in vec] for vec in vectors]
