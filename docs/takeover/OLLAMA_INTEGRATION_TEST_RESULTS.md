# SRU Assistant — Ollama Integration Test Results

**Document Version:** 1.0.0  
**Test Suite Focus:** Ollama Qwen3.5:4B Adapter, Response Parsing, Thinking Separation, and Grounded Generation  
**Target Environment:** Local Windows 10/11, Python 3.11.9, Ollama 0.30+, NVIDIA RTX 4050 (6GB VRAM)  

---

## 1. Overview of Added & Updated Tests

To ensure long-term regression safety, tests were expanded across unit and live integration suites:

### Unit Tests (`tests/generation/test_generators.py`):
These tests utilize mocked HTTP client responses to test adapter logic offline without requiring a live Ollama daemon:
1. `test_chat_endpoint_parsing_and_thinking_separation`: Validates that responses from `/api/chat` correctly extract student-facing content and isolate thinking traces.
2. `test_generate_endpoint_parsing_and_thinking_separation`: Validates that responses from `/api/generate` correctly extract answer text and isolate thinking traces.
3. `test_embedded_think_tag_stripping`: Validates that raw `<think>...</think>` tags embedded within response text are cleanly removed from the student answer and stored in `thinking`.
4. `test_token_limit_exhaustion_during_reasoning`: Validates that when Ollama halts with `done_reason="length"` during thinking, an actionable `GenerationError` is raised indicating token exhaustion.
5. `test_empty_response_actionable_diagnostic`: Validates that genuinely empty responses produce informative diagnostic messages identifying the model, prompt tokens, and done reason.

### Live Integration Tests (`tests/generation/test_ollama_live.py`):
These tests interact with the live Ollama daemon and installed models:
1. `test_qwen35_live_generation_non_empty`: Verifies that `qwen3.5:4b` generates clean, non-empty text without raw `<think>` tags when invoked directly.
2. `test_qwen35_grounded_answer_with_citations`: Verifies that `qwen3.5:4b` answers university queries inside the RAG pipeline with valid citations and grounding.
3. `test_health_endpoint_diagnostics_healthy`: Verifies that `/api/health` reports `llm_provider=ollama`, `llm_model=qwen3.5:4b`, and `llm_available=true`.

---

## 2. Live Academic Query Benchmark Results

The following live scenarios were executed using `scripts/test_live_qwen35.py`:

| Scenario | Query | Grounded | Citations Count | Pipeline Latency | Key Verification Outcome |
|---|---|:---:|:---:|:---:|---|
| **1. Exam Schedule** | *"When does Mid-Semester Examination I start for B.Tech VII semester?"* | **True** | 5 | ~22.6s | Successfully identified institutional date discrepancy between calendar sources (05-10 Oct vs 12-16 Sep). |
| **2. Credit Limits** | *"What is the maximum number of credits a student can register for in a semester under R23 regulations?"* | **True** | 3 | ~14.2s | Accurately extracted credit caps and semester registration limits from R23 regulations. |
| **3. Attendance Rules** | *"What are the minimum attendance requirements and what happens if attendance is below 75%?"* | **True** | 3 | ~16.6s | Verified 75% rule, medical condonation criteria (65%-74.9%), and mandatory detention (<65%). |
| **4. Unsupported Query** | *"What are the hostel mess charges and fee structure for the 2026 academic year?"* | **True** | 0 | ~4.6s | Safe refusal fallback triggered without hallucination or invented citations. |

---

## 3. Automated Test Execution Commands

Per user instructions, automated test commands are not executed directly by the assistant. Execute the following commands in PowerShell to run the complete test suite:

### A. Run Generator Unit Tests (Offline / Mocked)
```powershell
pytest tests/generation/test_generators.py -v
```

### B. Run Live Ollama Tests (Requires Ollama Daemon Running)
```powershell
pytest tests/generation/test_ollama_live.py -v
```

### C. Run Complete Regression Test Suite
```powershell
pytest -v
```

### D. Run Live End-to-End Qwen3.5:4B Scenario Validation Script
```powershell
python scripts/test_live_qwen35.py
```

