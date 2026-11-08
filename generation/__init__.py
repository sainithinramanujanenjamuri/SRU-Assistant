"""SRU Assistant - Generation package (prompts, LLM adapters, response synthesis)."""

from generation.llm import (
    BaseGenerator,
    DeterministicAnswerGenerator,
    OllamaLLMClient,
    get_generator,
)
from generation.models import (
    ContextBudgetExceededError,
    GenerationError,
    GenerationResponse,
    LLMProviderUnavailableError,
    RAGPromptContext,
    RAGResponse,
    RetrievedEvidence,
)
from generation.pipeline import BaselineRAGPipeline
from generation.prompts import (
    DEFAULT_SYSTEM_PROMPT,
    INSUFFICIENT_EVIDENCE_FALLBACK,
    ContextBuilder,
    GroundedPromptTemplate,
)

__all__ = [
    "DEFAULT_SYSTEM_PROMPT",
    "INSUFFICIENT_EVIDENCE_FALLBACK",
    "BaseGenerator",
    "BaselineRAGPipeline",
    "ContextBudgetExceededError",
    "ContextBuilder",
    "DeterministicAnswerGenerator",
    "GenerationError",
    "GenerationResponse",
    "GroundedPromptTemplate",
    "LLMProviderUnavailableError",
    "OllamaLLMClient",
    "RAGPromptContext",
    "RAGResponse",
    "RetrievedEvidence",
    "get_generator",
]
