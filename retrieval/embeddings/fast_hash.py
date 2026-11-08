"""Deterministic lexical-feature embedding baseline for offline operation, CI, and testing.

IMPORTANT ARCHITECTURAL NOTE:
This model is explicitly NOT a neural semantic embedding model and does NOT possess
semantic understanding of synonyms or natural-language meaning.
It is a deterministic lexical-feature projection model that maps token and character
subword n-grams into a fixed-dimensional unit vector using hash functions.
It is provided to ensure reliable, zero-network, sub-millisecond testing, continuous
integration, and reproducible baseline comparisons.
"""

import hashlib
import re
from collections.abc import Sequence

import numpy as np

from retrieval.embeddings.base import BaseEmbeddingModel


class FastHashEmbeddingModel(BaseEmbeddingModel):
    """Deterministic lexical-feature embedding baseline.

    Constructs dense, unit-normalized vectors by hashing word tokens and character
    subwords into a fixed-dimensional vector space with sign-hashing.
    """

    def __init__(self, dimension: int = 384, model_name: str = "fasthash-384"):
        if dimension <= 0:
            raise ValueError(f"Dimension must be positive, got {dimension}")
        self._dimension = dimension
        self._model_name = model_name
        self._token_pattern = re.compile(r"\b\w+\b", re.UNICODE)

    @property
    def provider_name(self) -> str:
        return "fasthash"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def _hash_feature(self, feature: str) -> tuple[int, float]:
        """Hash a token or subword into a bucket index and a {-1.0, +1.0} sign."""
        digest = hashlib.md5(feature.encode("utf-8")).digest()
        # First 4 bytes determine index
        bucket = int.from_bytes(digest[:4], byteorder="little") % self._dimension
        # 5th byte determines sign to cancel out hash collision bias (Count-Min sketch property)
        sign = 1.0 if (digest[4] % 2 == 0) else -1.0
        return bucket, sign

    def _embed_single(self, text: str) -> list[float]:
        cleaned = self.validate_text(text).lower()
        vec = np.zeros(self._dimension, dtype=np.float32)

        # Extract word tokens
        tokens = self._token_pattern.findall(cleaned)
        if not tokens:
            # Fallback for purely symbolic strings
            tokens = [cleaned]

        for token in tokens:
            # Whole word feature with higher weight
            idx, sign = self._hash_feature(token)
            vec[idx] += 2.0 * sign

            # Character 3-grams and 4-grams for subword / morphological overlap
            if len(token) >= 3:
                for n in (3, 4):
                    for i in range(len(token) - n + 1):
                        ngram = token[i : i + n]
                        idx_ng, sign_ng = self._hash_feature(ngram)
                        vec[idx_ng] += 1.0 * sign_ng

        # Bigram features for adjacent terms
        for i in range(len(tokens) - 1):
            bigram = f"{tokens[i]}_{tokens[i + 1]}"
            idx_bg, sign_bg = self._hash_feature(bigram)
            vec[idx_bg] += 1.5 * sign_bg

        return self.normalize_vector(vec)

    def embed_text(self, text: str) -> list[float]:
        """Generate a unit-normalized lexical-feature vector for single text input."""
        return self._embed_single(text)

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate unit-normalized lexical-feature vectors for a sequence of text inputs."""
        if not texts:
            return []
        return [self._embed_single(t) for t in texts]
