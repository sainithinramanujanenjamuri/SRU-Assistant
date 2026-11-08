# Baseline Test Results

**Date & Time:** 2026-11-05 05:25:49 IST  
**Host Environment:** Windows (Win32), Python 3.11.9, pytest 9.0.2  
**Command Executed:**
```powershell
$env:DEBUG="true"; pytest -v
```

---

## 1. Summary Statistics

- **Total Test Items Collected:** 324
- **Passed:** 314
- **Failed:** 2
- **Skipped:** 8
- **Warnings:** 1 (Starlette `BlockingPortal` deprecation warning)
- **Duration:** 48.16 seconds
- **Exit Code:** 1

---

## 2. Initial Environment & Import Issues Encountered

Prior to executing the full test suite, two environment/configuration hurdles were encountered and resolved:

1. **Missing Runtime Dependency `python-multipart`**:
   - Encountered during test collection in `tests/test_api.py`, `tests/generation/test_ollama_live.py`, and `tests/test_reliability_security.py`.
   - Root Cause: FastAPI's `/documents/upload` route imports form parsing utilities requiring `python-multipart`. Although declared in `requirements.txt` (`python-multipart>=0.0.9`), it was omitted from `pyproject.toml` dependencies and was not installed in the active environment.
   - Action: Installed `python-multipart` via `pip install python-multipart==0.0.33`.

2. **Environment Variable Conflict on `DEBUG`**:
   - The user OS environment variable `DEBUG` was set to the string `"release"`.
   - Root Cause: `pydantic-settings` BaseSettings attempts to parse `DEBUG` as a boolean (`debug: bool = Field(default=True)`). Pydantic's boolean parser failed with `ValidationError: Input should be a valid boolean, unable to interpret input 'release'`.
   - Immediate Workaround for Baseline: Set `$env:DEBUG="true"` in the PowerShell test session to run the baseline without altering source code.
   - Planned Permanent Fix (Phase 2): Implement a field validator in `app/config/settings.py` to gracefully accept standard non-boolean environment strings (such as `release`, `prod`, `dev`) without crashing.

---

## 3. Failure Details

### Failure 1: Missing Model Status Check on Inactive Daemon
- **Test:** `tests/generation/test_generators.py::TestOllamaLLMClient::test_status_check_on_missing_model`
- **Location:** `tests/generation/test_generators.py:89`
- **Assertion:**
  ```python
  client = OllamaLLMClient(model_name="nonexistent-model-xyz:99b", base_url="http://localhost:11434")
  available, msg = client.is_available()
  assert available is False
  assert "not pulled" in msg
  ```
- **Observed Result:**
  ```
  AssertionError: assert 'not pulled' in "Cannot connect to Ollama daemon at http://localhost:11434. Please ensure Ollama is running (e.g. 'ollama serve')."
  ```
- **Root Cause:** The test assumed the Ollama daemon was running and reachable at `http://localhost:11434`. When the daemon is offline, `is_available()` returns a connection error message rather than probing model tags.

### Failure 2: Live Installed Model Availability Test on Inactive Daemon
- **Test:** `tests/generation/test_generators.py::TestOllamaLLMClient::test_live_installed_model_availability`
- **Location:** `tests/generation/test_generators.py:95`
- **Assertion:**
  ```python
  client = OllamaLLMClient(model_name="qwen2.5:0.5b", base_url="http://localhost:11434")
  available, msg = client.is_available()
  assert available is True
  ```
- **Observed Result:**
  ```
  AssertionError: assert False is True
  ```
- **Root Cause:** The test directly asserted that a live local Ollama service with `qwen2.5:0.5b` was online and returned `available is True`. In an environment where the daemon is stopped, this test unconditionally fails.

---

## 4. Skipped Tests (External Service Gated)

All 8 skipped tests occurred in `tests/generation/test_ollama_live.py`. These tests correctly employ a fixture (`ensure_ollama_available`) that probes the live daemon and cleanly skips when the daemon is offline:

- `test_ollama_live.py:44`: Missing model actionable message
- `test_ollama_live.py:55`: Full prompt generation with Qwen (2 parametrized tests)
- `test_ollama_live.py:70`: Exact factual grounding verification
- `test_ollama_live.py:100`: Insufficient evidence refusal behavior
- `test_ollama_live.py:123`: Citation integrity and page provenance
- `test_ollama_live.py:149`: End-to-end API query resolution with Ollama
- `test_ollama_live.py:180`: Pipeline diagnostic latency breakdown

---

## 5. Baseline Conclusions

1. Core logic, tokenization, loaders (PDF, DOCX, TXT), cleaners, structure detectors, chunking, BM25 indexing, vector store operations, hybrid reciprocal rank fusion, metadata filtering, reranking, context building, grounded prompt templates, conflict detection, claim extraction, citation verification, and FastAPI routing passed 314 tests cleanly.
2. The only 2 failures stem from assumptions that an Ollama service daemon is active during unit test runs in `tests/generation/test_generators.py`.
3. In Phase 2 & Phase 9, these tests will be adjusted to properly distinguish between daemon unavailability and model status, and unit tests will mock network responses where appropriate while retaining live integration tests for live environments.

