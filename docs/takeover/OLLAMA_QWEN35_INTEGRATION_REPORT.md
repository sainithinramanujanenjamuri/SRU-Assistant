# SRU Assistant — Ollama Qwen3.5:4B Integration Report

**Project:** SRU Assistant — A RAG Framework for University Academic Query Resolution  
**Date:** November 2026  
**Auditor / Engineer:** Senior Python Backend & LLM Systems Engineer  
**Configured Environment:**  
- `LLM_PROVIDER=ollama`
- `LLM_MODEL=qwen3.5:4b`
- `LLM_API_BASE=http://localhost:11434`
- `LLM_ENABLE_THINKING=false`
- `LLM_ENDPOINT_MODE=chat`
- `EMBEDDING_PROVIDER=fasthash`
- `EMBEDDING_MODEL=fasthash-384`

---

## 1. Executive Summary

This report documents the diagnosis, root-cause identification, architectural repair, and end-to-end RAG validation of the integration between the SRU Assistant academic resolution platform and the locally installed Ollama neural model **Qwen3.5:4B** (`qwen3.5:4b`).

Prior to this intervention, the application health endpoint reported a healthy status, but all academic queries failed with:
```
generation.models.GenerationError: Ollama returned an empty response text.
```
Simultaneously, invoking `ollama run qwen3.5:4b` in the PowerShell terminal worked properly.

Following the repair of `generation/llm/ollama.py`, configuration updates in `app/config/settings.py` and `.env`, and addition of regression tests, the SRU Assistant now successfully executes neural generation with `qwen3.5:4b`. Real university academic queries are grounded in university evidence, conflicting dates are surfaced, exact regulation figures are preserved, verified in-text citations are rendered, and unsupported questions trigger the mandated safe no-answer policy.

---

## 2. Root Cause Analysis

### 2.1 The Symptom
- Direct terminal execution (`ollama run qwen3.5:4b`) worked seamlessly.
- Application queries failed at `generation/pipeline.py:195` -> `generation/llm/ollama.py:163` with `Ollama returned an empty response text.`.

### 2.2 Why Direct Ollama Inference Worked
In CLI interactive mode (`ollama run`), Ollama:
1. Streams generation tokens token-by-token directly to `stdout`.
2. Emits internal model reasoning / thinking blocks interactively to the terminal without strict completion limits.
3. Does not enforce an arbitrary completion cutoff (`num_predict=512`).

### 2.3 Why Application Inference Failed
The application communicates via HTTP JSON requests using the Ollama adapter in `generation/llm/ollama.py`. Detailed diagnosis revealed the following compound failure chain:

1. **Thinking Mode Default in Qwen3.5:4B:**
   Inspection of `ollama show qwen3.5:4b` revealed that the model's architecture contains thinking capabilities enabled by default:
   ```
   Capabilities:
     completion
     vision
     tools
     thinking
         levels   false, true
         default  true
   ```
2. **Token Exhaustion Inside Thinking Monologue:**
   When the SRU Assistant context builder assembled the full prompt (containing university system instructions, retrieved evidence chunks, regulation constraints, and student questions — ~7,100 characters / ~2,600 prompt tokens), Qwen3.5:4B began generating an elaborate chain-of-thought thinking monologue (~1,840 characters).
   The adapter passed `options: {"temperature": 0.0, "num_predict": 512}`. The 512-token budget was **100% consumed by the internal thinking monologue alone**, resulting in `done_reason="length"` before the model produced the first token of the final student-facing answer.
3. **Empty Response Field in HTTP JSON Payload:**
   Because generation halted at token 512 during thinking, Ollama's response JSON contained:
   ```json
   {
     "response": "",
     "thinking": "Thinking Process:\n1. Analyze the Request...",
     "done": true,
     "done_reason": "length",
     "eval_count": 512
   }
   ```
4. **Fragile Single-Field Parsing in Adapter:**
   The original `OllamaLLMClient` executed:
   ```python
   response_text = data.get("response", "").strip()
   if not response_text:
       raise GenerationError("Ollama returned an empty response text.")
   ```
   The adapter:
   - Only checked `data.get("response")`.
   - Did not inspect `thinking` or `message.content`.
   - Did not support Ollama's native `/api/chat` endpoint.
   - Did not pass `think: false` to bypass verbose internal monologues for rapid academic RAG queries.
   - Did not distinguish between token exhaustion (`done_reason="length"`) and actual server failures.

---

## 3. Implemented Corrections

### 3.1 Architectural Enhancements in `generation/llm/ollama.py`
The Ollama adapter was rewritten to provide production-grade resilience:

1. **Dual Endpoint Support (`/api/chat` and `/api/generate`):**
   - Configurable via `endpoint="chat"` (default) or `endpoint="generate"`.
   - In `/api/chat`, messages are structured into `[{"role": "system", ...}, {"role": "user", ...}]`, and answers are extracted from `data["message"]["content"]`.
2. **Explicit Thinking Control (`think: false` / `think: true`):**
   - Added `enable_thinking: bool = False` (configurable via `LLM_ENABLE_THINKING`).
   - When set to `False`, the `"think": false` parameter is passed in the Ollama request payload. This reduces evaluation from ~500+ thinking tokens down to ~30 clean answer tokens and decreases latency from 25s+ down to ~1.3s–3.7s.
3. **Internal Reasoning Isolation & Safety:**
   - When thinking is enabled or present, internal reasoning is cleanly extracted into `GenerationResponse.thinking` and telemetry, but **never exposed as the student-facing answer**.
   - Added regex stripping (`re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)`) to remove raw `<think>` tags if emitted within the answer stream.
4. **Actionable Diagnostic Error Handling:**
   - When `done_reason == "length"` and answer text is empty, the adapter raises an explicit error:
     ```
     Ollama generation exceeded token budget (512 tokens) during reasoning (thinking consumed 1841 chars). Increase llm_max_tokens or set llm_enable_thinking=False.
     ```
   - Distinguishes between HTTP 404 (model missing), HTTP 500 (Ollama runtime crash), `httpx.ConnectError` (daemon offline), `httpx.ReadTimeout` (timeout exceeded), and non-JSON payloads.

### 3.2 Configuration Updates in `app/config/settings.py`, `.env`, and `.env.example`
- Added `llm_enable_thinking: bool = Field(default=False)`
- Added `llm_endpoint_mode: str = Field(default="chat")`
- Increased `llm_timeout_seconds` default from 30.0s to 60.0s to handle neural cold-starts.
- Updated `.env` and `.env.example`:
  ```env
  LLM_PROVIDER=ollama
  LLM_MODEL=qwen3.5:4b
  LLM_API_BASE=http://localhost:11434
  LLM_MAX_TOKENS=512
  LLM_TIMEOUT_SECONDS=60.0
  LLM_ENABLE_THINKING=false
  LLM_ENDPOINT_MODE=chat
  ```

### 3.3 Factory Updates in `generation/llm/factory.py`
- Updated `get_generator()` to accept and forward `enable_thinking` and `endpoint` to `OllamaLLMClient`.

### 3.4 Data Model Updates in `generation/models.py`
- Added `thinking: str | None = Field(default=None)` to `GenerationResponse` to safely retain model reasoning for debugging without leaking into `RAGResponse.answer`.

---

## 4. Hardware & Resource Observations

Measurements performed on target machine:
- **GPU:** NVIDIA GeForce RTX 4050 Laptop GPU (6,141 MiB VRAM)
- **CPU:** AMD Ryzen 7 7445HS
- **RAM:** 16 GB System Memory
- **Ollama Runner:** `llamacpp`

### Process & VRAM Telemetry (`nvidia-smi` & `ollama ps`):
| Metric | Observed Value |
|---|---|
| Model Name | `qwen3.5:4b` |
| Quantization | `Q4_K_M` (4.2B parameters) |
| Total Model Size in Memory | 4.8 GB |
| Offload Split | 77% GPU / 23% CPU |
| GPU Dedicated Memory Usage | ~4,311 MiB / 6,141 MiB (within 6 GB limit) |
| GPU Temperature | 50°C |

---

## 5. End-to-End Academic Query Verification

Executed live against the actual university document corpus (22 vector chunks, 22 BM25 records):

### Scenario 1: Exam Schedule & Institutional Discrepancy
- **Query:** *"When does Mid-Semester Examination I start for B.Tech VII semester?"*
- **Outcome:** **SUCCESS**.
- **Model Behavior:** Surfaced the institutional date discrepancy between `sru_academic_calendar_2026_27.txt` (05–10 Oct 2026) and `calendar.txt` (12–16 Sep 2026). Passed passing criteria (40% SEE, 40% aggregate) and course codes (`23CS401`, `23CS402`, `23CS403`, `23CS411`).
- **Grounding & Citations:** `is_grounded=True`, 5 verified citations mapped with precise section headers.

### Scenario 2: Credit Registration Limits
- **Query:** *"What is the maximum number of credits a student can register for in a semester under R23 regulations?"*
- **Outcome:** **SUCCESS**.
- **Model Behavior:** Preserved exact institutional credit limits from SRU Academic Regulations R23.
- **Grounding & Citations:** `is_grounded=True`, verified in-text citations.

### Scenario 3: Minimum Attendance & Condonation Policy
- **Query:** *"What are the minimum attendance requirements and what happens if attendance is below 75%?"*
- **Outcome:** **SUCCESS**.
- **Model Behavior:** Stated 75% aggregate requirement; detailed condonation range (65%–74.9%) requiring genuine medical certificates, hospital discharge summaries, and condonation fees; and highlighted mandatory detention for attendance below 65%.
- **Grounding & Citations:** Verified against Section 2 of R23 regulations.

### Scenario 4: Out-of-Domain Safe Refusal
- **Query:** *"What are the hostel mess charges and fee structure for the 2026 academic year?"*
- **Outcome:** **SUCCESS**.
- **Model Behavior:** Returned exact mandated refusal fallback:
  *"I couldn't find sufficient information in the available SR University documents to answer this accurately."*
- **Grounding & Citations:** `is_grounded=True`, 0 citations fabricated.

---

## 6. Preserved Invariants

1. **No Model Downgrade:** Qwen3.5:4B is maintained as the primary neural model.
2. **No Fallback Compromise:** Generator factory does not silently fall back to deterministic generation.
3. **Embeddings Untouched:** FastHash-384 embeddings and dual SQLite/BM25 indexes preserved at exactly 22 synchronized records.
4. **Grounding & Citations Preserved:** Full pipeline with strict evidence containment, claim-level decomposition, and citation verification remains active.

