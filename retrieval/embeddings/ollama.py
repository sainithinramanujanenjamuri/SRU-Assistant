"""Ollama embedding model adapter communicating with local Ollama daemon."""

from collections.abc import Sequence
from typing import Any

import httpx

from retrieval.embeddings.base import BaseEmbeddingModel
from retrieval.models import EmbeddingError, EmbeddingProviderUnavailableError


class OllamaEmbeddingModel(BaseEmbeddingModel):
    """Adapter for neural embedding models served locally via Ollama."""

    def __init__(
        self,
        model_name: str = "nomic-embed-text",
        base_url: str = "http://localhost:11434",
        dimension: int = 768,
        timeout_seconds: float = 30.0,
    ):
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._dimension = dimension
        self._timeout = timeout_seconds

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def is_available(self) -> tuple[bool, str]:
        """Check if the Ollama server is reachable and whether the configured model is installed."""
        url = f"{self._base_url}/api/tags"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(url)
                if res.status_code != 200:
                    return False, f"Ollama returned HTTP {res.status_code}"
                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]
                # Check exact or prefix match (e.g., 'nomic-embed-text:latest' vs 'nomic-embed-text')
                found = any(m == self._model_name or (m and m.startswith(f"{self._model_name}:")) for m in models)
                if not found:
                    return False, f"Ollama is running, but model '{self._model_name}' is not pulled (available: {models})"
                return True, "Available"
        except httpx.ConnectError:
            return False, f"Cannot connect to Ollama at {self._base_url}. Daemon may not be running."
        except Exception as e:
            return False, f"Error checking Ollama status: {e}"

    def _call_ollama(self, text: str) -> list[float]:
        cleaned = self.validate_text(text)
        embed_url = f"{self._base_url}/api/embed"
        legacy_url = f"{self._base_url}/api/embeddings"

        # Try /api/embed first (Ollama >= 0.1.34)
        payload: dict[str, Any] = {"model": self._model_name, "input": cleaned}
        try:
            with httpx.Client(timeout=self._timeout) as client:
                res = client.post(embed_url, json=payload)
                if res.status_code == 200:
                    data = res.json()
                    embeddings = data.get("embeddings", [])
                    if embeddings and len(embeddings) > 0:
                        vec = embeddings[0]
                        return self._validate_and_normalize(vec)

                # If /api/embed returned 404 or 501, try legacy /api/embeddings
                if res.status_code in (404, 501):
                    legacy_payload = {"model": self._model_name, "prompt": cleaned}
                    legacy_res = client.post(legacy_url, json=legacy_payload)
                    if legacy_res.status_code == 200:
                        legacy_data = legacy_res.json()
                        vec = legacy_data.get("embedding", [])
                        if vec:
                            return self._validate_and_normalize(vec)
                    res = legacy_res

                # Handle failure status
                if res.status_code == 404:
                    raise EmbeddingError(
                        f"Ollama model '{self._model_name}' not found. Run 'ollama pull {self._model_name}'."
                    )
                raise EmbeddingError(
                    f"Ollama embedding request failed with HTTP {res.status_code}: {res.text}"
                )
        except httpx.ConnectError as e:
            raise EmbeddingProviderUnavailableError(
                f"Cannot connect to Ollama server at {self._base_url}: {e}"
            ) from e
        except httpx.TimeoutException as e:
            raise EmbeddingError(f"Ollama embedding request timed out after {self._timeout}s: {e}") from e

    def _validate_and_normalize(self, raw_vec: list[float]) -> list[float]:
        if not raw_vec or not isinstance(raw_vec, list):
            raise EmbeddingError(f"Ollama returned invalid vector structure: {type(raw_vec)}")
        # Check dimensionality
        if len(raw_vec) != self._dimension:
            # Auto-update if dimension was default placeholder and not locked
            if self._dimension == 768 and len(raw_vec) != 768:
                self._dimension = len(raw_vec)
            else:
                raise EmbeddingError(
                    f"Vector dimension mismatch from Ollama: expected {self._dimension}, got {len(raw_vec)}"
                )
        return self.normalize_vector(raw_vec)

    def embed_text(self, text: str) -> list[float]:
        """Generate a unit-normalized embedding vector for single text via Ollama."""
        return self._call_ollama(text)

    def embed_batch(self, texts: Sequence[str]) -> list[list[float]]:
        """Generate unit-normalized embedding vectors for batch via Ollama."""
        if not texts:
            return []
        cleaned_texts = [self.validate_text(t) for t in texts]
        embed_url = f"{self._base_url}/api/embed"

        # Attempt batch call on /api/embed
        try:
            with httpx.Client(timeout=self._timeout * max(1, len(texts) // 10 + 1)) as client:
                res = client.post(embed_url, json={"model": self._model_name, "input": cleaned_texts})
                if res.status_code == 200:
                    data = res.json()
                    embeddings = data.get("embeddings", [])
                    if len(embeddings) == len(cleaned_texts):
                        return [self._validate_and_normalize(v) for v in embeddings]
        except (httpx.ConnectError, httpx.TimeoutException):
            raise
        except Exception:
            pass

        # Fallback to item-by-item if batch endpoint unsupported
        return [self._call_ollama(t) for t in cleaned_texts]
