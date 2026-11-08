"""Modular tokenization abstraction for SRU Assistant (Phase 2).

Provides a lightweight, deterministic token counter and tokenizer without
depending on any specific LLM, embedding model, or heavy ML runtime.
"""

import re
from abc import ABC, abstractmethod


class BaseTokenizer(ABC):
    """Abstract interface for document and chunk tokenizers."""

    @abstractmethod
    def tokenize(self, text: str) -> list[str]:
        """Split text into a sequence of token strings."""

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text."""


class RegexTokenizer(BaseTokenizer):
    """Deterministic regex-based word and punctuation tokenizer.

    Calibrated to separate alphanumeric words and individual punctuation marks,
    closely approximating standard subword token counts without external libraries.
    """

    # Matches word characters (including numbers) or any single non-whitespace punctuation
    TOKEN_PATTERN = re.compile(r"\w+|[^\w\s]", re.UNICODE)

    def tokenize(self, text: str) -> list[str]:
        """Split text into words and punctuation tokens."""
        if not text:
            return []
        return self.TOKEN_PATTERN.findall(text)

    def count_tokens(self, text: str) -> int:
        """Count tokens using regex matching."""
        if not text:
            return 0
        return len(self.tokenize(text))


_default_tokenizer = RegexTokenizer()


def get_default_tokenizer() -> BaseTokenizer:
    """Return the default tokenizer instance."""
    return _default_tokenizer
