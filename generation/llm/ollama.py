"""Ollama LLM client adapter communicating with local Ollama service."""
from __future__ import annotations

import re
import time
from typing import Any

import httpx

from generation.llm.base import BaseGenerator
from generation.models import GenerationError, GenerationResponse, LLMProviderUnavailableError


class OllamaLLMClient(BaseGenerator):
    """Neural LLM generation adapter connecting to local Ollama service.

    Supports both `/api/chat` and `/api/generate` endpoints, optional system prompts,
    robust thinking-block separation, raw `<think>` tag stripping, and actionable error
    diagnostics across all Ollama model architectures (including Qwen3.5 and Qwen2.5).
    """

    def __init__(
        self,
        model_name: str = "qwen2.5:0.5b",
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 60.0,
        temperature: float = 0.0,
        max_tokens: int = 512,
        top_p: float | None = None,
        enable_thinking: bool = False,
        endpoint: str = "chat",
    ):
        self._model_name = model_name
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._top_p = top_p
        self._enable_thinking = enable_thinking
        self._endpoint = endpoint.lower().strip() if endpoint else "chat"

    @property
    def provider_name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def base_url(self) -> str:
        return self._base_url

    @property
    def temperature(self) -> float:
        return self._temperature

    @property
    def max_tokens(self) -> int:
        return self._max_tokens

    @property
    def top_p(self) -> float | None:
        return self._top_p

    @property
    def enable_thinking(self) -> bool:
        return self._enable_thinking

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def is_llm(self) -> bool:
        return True

    def is_available(self) -> tuple[bool, str]:
        """Check whether the Ollama daemon is reachable and whether the configured model is installed."""
        url = f"{self._base_url}/api/tags"
        try:
            with httpx.Client(timeout=5.0) as client:
                res = client.get(url)
                if res.status_code != 200:
                    return False, f"Ollama returned HTTP {res.status_code}: {res.text}"
                data = res.json()
                models = [m.get("name") for m in data.get("models", [])]

                target_base = self._model_name.split(":")[0].lower()
                target_full = self._model_name.lower()

                found = False
                for m in models:
                    if not m:
                        continue
                    m_lower = m.lower()
                    m_base = m_lower.split(":")[0]
                    # Direct match or full match with tag
                    if m_lower == target_full or m_lower.startswith(f"{target_full}:"):
                        found = True
                        break
                    # If target specified without tag (or :latest), match against model with tag
                    if ":" not in self._model_name or self._model_name.endswith(":latest"):
                        if m_base == target_base or m_lower == f"{target_base}:latest":
                            found = True
                            break
                    # If target specified with tag, match against model with matching base and tag
                    if m_base == target_base and m_lower.endswith(f":{self._model_name.split(':')[-1].lower()}"):
                        found = True
                        break

                if not found:
                    available_str = ", ".join(models) if models else "None"
                    return (
                        False,
                        f"Ollama is running at {self._base_url}, but model '{self._model_name}' is not pulled. "
                        f"Run 'ollama pull {self._model_name}' first (available: [{available_str}])",
                    )
                return True, "Available"
        except httpx.ConnectError:
            return (
                False,
                f"Cannot connect to Ollama daemon at {self._base_url}. "
                f"Please ensure Ollama is running (e.g. 'ollama serve').",
            )
        except httpx.TimeoutException as e:
            return (
                False,
                f"Timed out connecting to Ollama daemon at {self._base_url}: {e}.",
            )
        except Exception as e:
            return False, f"Error checking Ollama status: {e}"

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        enable_thinking: bool | None = None,
    ) -> GenerationResponse:
        """Call Ollama (/api/chat or /api/generate) to produce a grounded response."""
        t0 = time.perf_counter()

        actual_max_tokens = max_tokens if max_tokens is not None else self._max_tokens
        actual_temperature = temperature if temperature is not None else self._temperature
        actual_top_p = top_p if top_p is not None else self._top_p
        actual_think = enable_thinking if enable_thinking is not None else self._enable_thinking

        options: dict[str, Any] = {
            "temperature": actual_temperature,
            "num_predict": actual_max_tokens,
        }
        if actual_top_p is not None:
            options["top_p"] = actual_top_p

        is_chat = self._endpoint in ("chat", "auto")
        if is_chat:
            url = f"{self._base_url}/api/chat"
            messages: list[dict[str, str]] = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            payload: dict[str, Any] = {
                "model": self._model_name,
                "messages": messages,
                "stream": False,
                "options": options,
            }
            if actual_think is not None:
                payload["think"] = actual_think
        else:
            url = f"{self._base_url}/api/generate"
            payload = {
                "model": self._model_name,
                "prompt": prompt,
                "stream": False,
                "options": options,
            }
            if system_prompt:
                payload["system"] = system_prompt
            if actual_think is not None:
                payload["think"] = actual_think

        try:
            with httpx.Client(timeout=self._timeout) as client:
                res = client.post(url, json=payload)
                if res.status_code == 404:
                    raise LLMProviderUnavailableError(
                        f"Ollama model '{self._model_name}' not found on {self._base_url}. "
                        f"Run 'ollama pull {self._model_name}' first."
                    )
                if res.status_code != 200:
                    raise GenerationError(
                        f"Ollama generation request failed with HTTP {res.status_code}: {res.text}"
                    )

                try:
                    data = res.json()
                except Exception as e:
                    raise GenerationError(
                        f"Ollama returned non-JSON response (HTTP {res.status_code}): {res.text[:200]}"
                    ) from e

                # Extract response text and thinking trace based on returned payload structure
                if "message" in data and isinstance(data["message"], dict):
                    msg = data["message"]
                    raw_text = msg.get("content", "") or ""
                    thinking_trace = msg.get("thinking") or data.get("thinking") or ""
                else:
                    raw_text = data.get("response", "") or ""
                    thinking_trace = data.get("thinking") or ""

                done_reason = data.get("done_reason")

                # Parse and strip embedded <think>...</think> tags if present in the text
                if "<think>" in raw_text:
                    think_match = re.search(r"<think>(.*?)</think>", raw_text, flags=re.DOTALL)
                    if think_match:
                        extracted = think_match.group(1).strip()
                        if not thinking_trace:
                            thinking_trace = extracted
                        raw_text = re.sub(r"<think>.*?</think>", "", raw_text, flags=re.DOTALL)
                    else:
                        parts = raw_text.split("<think>", 1)
                        raw_text = parts[0]
                        if len(parts) > 1 and not thinking_trace:
                            thinking_trace = parts[1].replace("</think>", "").strip()

                cleaned_text = raw_text.strip()

                # Robust, actionable validation
                if not cleaned_text:
                    if done_reason == "length":
                        raise GenerationError(
                            f"Ollama generation exceeded token budget ({actual_max_tokens} tokens) during reasoning "
                            f"(thinking consumed {len(thinking_trace)} chars). "
                            f"Increase llm_max_tokens or set llm_enable_thinking=False."
                        )
                    prompt_eval = data.get("prompt_eval_count", 0)
                    raise GenerationError(
                        f"Ollama returned empty response text (model='{self._model_name}', "
                        f"done_reason='{done_reason}', prompt_eval_count={prompt_eval}, "
                        f"thinking_len={len(thinking_trace)})."
                    )

                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                prompt_eval_count = data.get("prompt_eval_count", 0)
                eval_count = data.get("eval_count", 0)

                return GenerationResponse(
                    text=cleaned_text,
                    model_name=self._model_name,
                    provider_name=self.provider_name,
                    is_llm=True,
                    prompt_tokens=prompt_eval_count,
                    completion_tokens=eval_count,
                    latency_ms=round(elapsed_ms, 2),
                    thinking=thinking_trace.strip() if thinking_trace else None,
                )
        except (httpx.ConnectError, httpx.ConnectTimeout) as e:
            raise LLMProviderUnavailableError(
                f"Cannot connect to Ollama service at {self._base_url}: {e}. "
                f"Ensure Ollama daemon is running ('ollama serve')."
            ) from e
        except httpx.TimeoutException as e:
            raise GenerationError(
                f"Ollama generation timed out after {self._timeout}s: {e}"
            ) from e


# Backward compatibility alias
OllamaGenerator = OllamaLLMClient
