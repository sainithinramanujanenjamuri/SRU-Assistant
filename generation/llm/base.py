"""Abstract base interface for answer generation backends."""
from __future__ import annotations



from abc import ABC, abstractmethod

from generation.models import GenerationResponse


class BaseGenerator(ABC):
    """Abstract interface defining answer generation backends."""

    @property

    @abstractmethod
    def provider_name(self) -> str:
        """Name of the generator provider (e.g. 'deterministic', 'ollama')."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Model or generator identifier."""
        pass

    @property
    @abstractmethod
    def is_llm(self) -> bool:
        """Flag indicating whether this generator is an actual neural LLM or a rule-based baseline."""
        pass

    @abstractmethod
    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> GenerationResponse:
        """Generate an answer given the prompt and optional system instructions.

        Raises:
            GenerationError: If generation fails.
            LLMProviderUnavailableError: If the remote LLM service cannot be reached.
        """
        pass

    @abstractmethod
    def is_available(self) -> tuple[bool, str]:
        """Check if the generator is available in the current environment."""
        pass
