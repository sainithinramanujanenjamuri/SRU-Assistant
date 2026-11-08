"""Academic-aware lexical tokenizer for BM25 retrieval.

Preserves institutional identifiers such as course codes (e.g., 23CSE302T),
regulations (e.g., R23), academic years (e.g., 2026-27), hyphenated academic terms,
dates, and academic acronyms while standardizing case and removing purely grammatical stop words.
"""

import re
from typing import Final

# Standard grammatical stop words (small, curated set that avoids removing numbers or query-critical terms)
STOP_WORDS: Final[set[str]] = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "in",
    "on",
    "at",
    "to",
    "for",
    "of",
    "with",
    "by",
    "from",
    "as",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "do",
    "does",
    "did",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
}

# Regex matching academic tokens:
# 1. Hyphenated academic years or terms: e.g., 2026-27, 2026-2027, mid-semester
# 2. Dot-delimited abbreviations: e.g., b.tech, m.tech, ph.d
# 3. Alphanumeric codes and words: e.g., 23cse302t, r23, cse, 12, september
ACADEMIC_TOKEN_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"\b[a-zA-Z0-9]+(?:[-.][a-zA-Z0-9]+)+\b|\b[a-zA-Z0-9]+\b"
)


class AcademicLexicalTokenizer:
    """Tokenizer specifically tuned for university academic documents and student queries.

    Ensures that course codes (23CSE302T), regulation IDs (R23), and session identifiers (2026-27)
    remain intact as unified tokens rather than fragmented across punctuation.
    """

    TOKENIZER_VERSION: Final[str] = "1.0.0"

    def __init__(self, filter_stop_words: bool = True, lowercase: bool = True):
        self.filter_stop_words = filter_stop_words
        self.lowercase = lowercase

    @property
    def version(self) -> str:
        """Return the tokenizer version for manifest verification."""
        return self.TOKENIZER_VERSION

    @staticmethod
    def _normalize_suffix(token: str) -> str:
        """Normalize simple English plurals without altering academic codes, numbers, or Latin root nouns."""
        if any(c.isdigit() or c in "-." for c in token) or len(token) <= 3:
            return token
        if token.endswith(("us", "is", "ss")):
            return token
        if token.endswith("ies") and len(token) > 4:
            return token[:-3] + "y"
        if token.endswith("es") and len(token) > 4 and token[-3] in ("s", "x", "z", "c", "h"):
            return token[:-2]
        if token.endswith("s"):
            return token[:-1]
        return token

    def tokenize(self, text: str) -> list[str]:
        """Tokenize input text into a list of academic-aware tokens.

        Args:
            text: Arbitrary query or chunk text string.

        Returns:
            List of normalized string tokens preserving course codes, dates, and identifiers.
        """
        if not text or not isinstance(text, str):
            return []

        # Find all matching tokens
        raw_tokens = ACADEMIC_TOKEN_PATTERN.findall(text)
        processed_tokens: list[str] = []

        for tok in raw_tokens:
            cleaned = tok.strip()
            if not cleaned:
                continue

            if self.lowercase:
                cleaned = cleaned.lower()

            # Remove trailing periods if present (e.g. end of sentence on a word)
            if cleaned.endswith(".") and not cleaned.startswith("."):
                cleaned = cleaned.rstrip(".")

            if not cleaned:
                continue

            # Candidate tokens to consider: the token itself plus subparts if hyphenated
            candidate_tokens = [cleaned]
            if "-" in cleaned:
                subparts = [p for p in cleaned.split("-") if p]
                candidate_tokens.extend(subparts)

            for cand in candidate_tokens:
                # Filter out grammatical stop words before suffix stripping
                has_digit_or_hyphen = any(c.isdigit() or c in "-." for c in cand)
                if self.filter_stop_words and not has_digit_or_hyphen and cand in STOP_WORDS:
                    continue

                processed_tokens.append(cand)

                # Also add singular/normalized form if different and not a stop word
                cand_normalized = self._normalize_suffix(cand)
                if cand_normalized != cand:
                    if not (self.filter_stop_words and cand_normalized in STOP_WORDS):
                        processed_tokens.append(cand_normalized)

        return processed_tokens
