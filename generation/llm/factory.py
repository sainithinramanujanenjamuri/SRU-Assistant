"""Factory function to instantiate generation backends based on configuration."""
from __future__ import annotations

from app.config.settings import get_settings
from generation.llm.base import BaseGenerator
from generation.llm.deterministic import DeterministicAnswerGenerator
from generation.llm.ollama import OllamaLLMClient


def get_generator(
    provider: str | None = None,
    model: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float | None = None,
    temperature: float | None = None,
    max_tokens: int | None = None,
    top_p: float | None = None,
    enable_thinking: bool | None = None,
    endpoint: str | None = None,
) -> BaseGenerator:
    """Instantiate and return the configured generator.


    IMPORTANT (Amendment 2):
    If an operator explicitly configures a specific provider (e.g. 'ollama'), that
    exact provider will be instantiated. The factory will NEVER silently fall back
    to the deterministic baseline if an explicitly chosen provider fails.
    """
    settings = get_settings()
    active_provider = (provider or settings.llm_provider).lower().strip()
    active_model = model or settings.llm_model
    active_url = base_url or settings.llm_api_base
    active_timeout = timeout_seconds or settings.llm_timeout_seconds
    active_temperature = temperature if temperature is not None else settings.llm_temperature
    active_max_tokens = max_tokens if max_tokens is not None else settings.llm_max_tokens
    active_top_p = top_p if top_p is not None else getattr(settings, "llm_top_p", None)
    active_thinking = (
        enable_thinking if enable_thinking is not None else getattr(settings, "llm_enable_thinking", False)
    )
    active_endpoint = endpoint or getattr(settings, "llm_endpoint_mode", "chat")

    if active_provider == "deterministic":
        return DeterministicAnswerGenerator(
            model_name=active_model or "rule-based-baseline-v1"
        )
    elif active_provider == "ollama":
        return OllamaLLMClient(
            model_name=active_model or "qwen2.5:0.5b",
            base_url=active_url,
            timeout_seconds=active_timeout,
            temperature=active_temperature,
            max_tokens=active_max_tokens,
            top_p=active_top_p,
            enable_thinking=active_thinking,
            endpoint=active_endpoint,
        )
    else:
        raise ValueError(
            f"Unsupported generator provider: '{active_provider}'. "
            f"Supported providers: 'deterministic' (rule-based baseline), 'ollama'."
        )
