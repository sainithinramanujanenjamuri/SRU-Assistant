"""Factory for instantiating configured candidate re-rankers."""
from __future__ import annotations


from typing import Any

from app.config.settings import get_settings
from retrieval.reranking.base import BaseReranker
from retrieval.reranking.deterministic import (
    DeterministicCrossEncoderReranker,
    DeterministicCrossFeatureReranker,
)
from retrieval.reranking.ollama import OllamaCrossEncoderReranker
from retrieval.reranking.passthrough import PassthroughReranker
from retrieval.reranking.transformer import TransformerCrossEncoderReranker


def get_reranker(
    method: str | None = None,
    model_name: str | None = None,
    **kwargs: Any,
) -> BaseReranker:
    """Instantiate and return a configured re-ranker instance.


    Args:
        method: Provider type ('deterministic', 'transformer', 'ollama', 'passthrough').
        model_name: Optional model identifier for neural or Ollama reranker.
        **kwargs: Additional provider-specific keyword arguments.

    Returns:
        Instance conforming to BaseReranker protocol.

    Raises:
        ValueError: If provider type is unrecognized.
    """
    settings = get_settings()
    provider_type = (method or settings.reranker_type).lower()
    target_model = model_name or settings.reranker_model_name

    if provider_type in ("deterministic", "deterministic_cross_feature", "deterministic_cross_encoder"):
        return DeterministicCrossFeatureReranker()
    elif provider_type in ("transformer", "sentence_transformers", "cross_encoder"):
        return TransformerCrossEncoderReranker(model_name=target_model)
    elif provider_type == "ollama":
        api_base = kwargs.get("api_base", settings.llm_api_base)
        timeout = kwargs.get("timeout_seconds", settings.llm_timeout_seconds)
        return OllamaCrossEncoderReranker(
            model_name=target_model,
            api_base=api_base,
            timeout_seconds=timeout,
        )
    elif provider_type in ("passthrough", "none", "identity"):
        return PassthroughReranker()
    else:
        raise ValueError(
            f"Unknown reranker provider '{method}'. "
            "Supported providers: 'deterministic', 'transformer', 'ollama', 'passthrough'."
        )


__all__ = [
    "BaseReranker",
    "DeterministicCrossEncoderReranker",
    "DeterministicCrossFeatureReranker",
    "OllamaCrossEncoderReranker",
    "PassthroughReranker",
    "TransformerCrossEncoderReranker",
    "get_reranker",
]
