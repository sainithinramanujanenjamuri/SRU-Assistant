"""Factory function to instantiate embedding models based on configuration."""
from __future__ import annotations



from app.config.settings import get_settings
from retrieval.embeddings.base import BaseEmbeddingModel
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.embeddings.ollama import OllamaEmbeddingModel
from retrieval.embeddings.sentence_transformers import SentenceTransformersEmbeddingModel


def get_embedding_model(
    provider: str | None = None,
    model_name: str | None = None,
    dimension: int | None = None,
    base_url: str | None = None,
    timeout_seconds: float | None = None,
) -> BaseEmbeddingModel:
    """Instantiate and return the configured embedding model.


    If parameters are omitted, values from application settings are used.
    """
    settings = get_settings()
    active_provider = (provider or settings.embedding_provider).lower().strip()
    active_model = model_name or settings.embedding_model
    active_dim = dimension or settings.embedding_dimension
    active_url = base_url or settings.embedding_ollama_base_url
    active_timeout = timeout_seconds or settings.embedding_timeout_seconds

    if active_provider == "fasthash":
        return FastHashEmbeddingModel(
            dimension=active_dim,
            model_name=active_model or "fasthash-384",
        )
    elif active_provider == "ollama":
        return OllamaEmbeddingModel(
            model_name=active_model or "nomic-embed-text",
            base_url=active_url,
            dimension=active_dim,
            timeout_seconds=active_timeout,
        )
    elif active_provider == "sentence_transformers":
        return SentenceTransformersEmbeddingModel(
            model_name=active_model or "all-MiniLM-L6-v2",
            dimension=active_dim,
        )
    else:
        raise ValueError(
            f"Unsupported embedding provider: '{active_provider}'. "
            f"Supported providers: 'fasthash', 'ollama', 'sentence_transformers'."
        )
