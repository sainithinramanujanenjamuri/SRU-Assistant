"""System and contextual prompt templates for academic query answering."""

from generation.prompts.context_builder import ContextBuilder
from generation.prompts.templates import (
    DEFAULT_SYSTEM_PROMPT,
    INSUFFICIENT_EVIDENCE_FALLBACK,
    GroundedPromptTemplate,
)

__all__ = [
    "DEFAULT_SYSTEM_PROMPT",
    "INSUFFICIENT_EVIDENCE_FALLBACK",
    "ContextBuilder",
    "GroundedPromptTemplate",
]
