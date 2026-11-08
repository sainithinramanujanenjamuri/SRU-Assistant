"""Ollama-based local LLM candidate re-ranking adapter."""

from collections.abc import Sequence
from typing import Any

from retrieval.models import RerankerUnavailableError, RerankResult
from retrieval.reranking.base import BaseReranker


class OllamaCrossEncoderReranker(BaseReranker):
    """Local LLM candidate re-ranking adapter using an Ollama instance.

    Uses zero-shot relevance evaluation against a local Ollama model (e.g., 'qwen3.5:0.8b').
    If Ollama daemon is unreachable or the requested model is missing,
    raises RerankerUnavailableError explicitly without silent fallback.
    """

    reranker_name: str = "ollama"
    reranker_provider: str = "ollama"

    def __init__(
        self,
        model_name: str = "qwen3.5:0.8b",
        api_base: str = "http://localhost:11434",
        timeout_seconds: float = 30.0,
    ):
        self.reranker_model = model_name
        self.api_base = api_base.rstrip("/")
        self.timeout = timeout_seconds

    def _check_availability(self) -> None:
        """Verify Ollama service is reachable and configured model exists."""
        import httpx

        try:
            resp = httpx.get(f"{self.api_base}/api/tags", timeout=5.0)
            if resp.status_code != 200:
                raise RerankerUnavailableError(
                    f"Ollama service returned unexpected HTTP {resp.status_code} from {self.api_base}"
                )
            data = resp.json()
            models = [m.get("name") for m in data.get("models", [])]
            # Match model name with or without tag suffix
            base_target = self.reranker_model.split(":")[0]
            matched = any(m == self.reranker_model or (m and m.split(":")[0] == base_target) for m in models)
            if not matched:
                raise RerankerUnavailableError(
                    f"Configured Ollama model '{self.reranker_model}' not found in installed models: {models}"
                )
        except httpx.RequestError as e:
            raise RerankerUnavailableError(
                f"Cannot connect to Ollama service at '{self.api_base}': {e}. Ensure Ollama is running."
            ) from e

    def rerank(
        self,
        query: str,
        candidates: Sequence[Any],
        top_k: int = 5,
    ) -> list[RerankResult]:
        """Re-rank candidates via Ollama LLM relevance scoring."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        if not candidates:
            return []

        self._check_availability()

        import httpx

        scored: list[dict[str, Any]] = []

        for rank, cand in enumerate(candidates, start=1):
            text = getattr(cand, "text", "")
            prompt = (
                f"On a scale from 0 to 10, rate how directly and accurately the following university document passage "
                f"answers the question. Respond ONLY with a single numeric number between 0 and 10.\n\n"
                f"Question: {query}\n"
                f"Passage: {text[:400]}\n\n"
                f"Rating (0-10):"
            )

            try:
                resp = httpx.post(
                    f"{self.api_base}/api/generate",
                    json={
                        "model": self.reranker_model,
                        "prompt": prompt,
                        "stream": False,
                        "options": {"temperature": 0.0, "num_predict": 5},
                    },
                    timeout=self.timeout,
                )
                resp.raise_for_status()
                out_text = resp.json().get("response", "").strip()
                import re
                num_match = re.search(r"(\d+(?:\.\d+)?)", out_text)
                if num_match:
                    raw_val = float(num_match.group(1))
                    norm_score = max(0.0, min(1.0, round(raw_val / 10.0, 6)))
                else:
                    norm_score = 0.5
            except Exception as e:
                raise RerankerUnavailableError(f"Ollama generation failed during reranking: {e}") from e

            scored.append({
                "cand": cand,
                "chunk_id": getattr(cand, "chunk_id", str(rank)),
                "document_id": getattr(cand, "document_id", "unknown_doc"),
                "text": text,
                "initial_rank": rank,
                "initial_score": getattr(
                    cand, "normalized_fused_score",
                    getattr(cand, "normalized_score", getattr(cand, "score", 0.0))
                ),
                "rerank_score": norm_score,
                "metadata": getattr(cand, "metadata", {}) or {},
                "provenance": getattr(cand, "provenance", {}) or {},
            })

        scored.sort(key=lambda x: (-x["rerank_score"], str(x["chunk_id"])))

        results: list[RerankResult] = []
        for rerank_rank, item in enumerate(scored[:top_k], start=1):
            cand = item["cand"]
            init_rank = item["initial_rank"]
            results.append(
                RerankResult(
                    chunk_id=item["chunk_id"],
                    document_id=item["document_id"],
                    text=item["text"],
                    rerank_score=item["rerank_score"],
                    initial_score=item["initial_score"],
                    initial_rank=init_rank,
                    rerank_rank=rerank_rank,
                    rank_delta=init_rank - rerank_rank,
                    reranker_name=self.reranker_name,
                    reranker_provider=self.reranker_provider,
                    reranker_model=self.reranker_model,
                    dense_score=getattr(cand, "dense_score", None),
                    dense_rank=getattr(cand, "dense_rank", None),
                    lexical_score=getattr(cand, "lexical_score", None),
                    lexical_rank=getattr(cand, "lexical_rank", None),
                    initial_hybrid_rank=getattr(cand, "initial_hybrid_rank", init_rank),
                    original_retrieval_mode=getattr(cand, "fusion_method", "hybrid"),
                    metadata=item["metadata"],
                    provenance=item["provenance"],
                )
            )

        return results
