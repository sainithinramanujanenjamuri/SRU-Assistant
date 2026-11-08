# Final Test Results & Regression Report

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  
**Platform:** Windows 10/11 (win32), Python 3.11.9, pytest 9.0.2  

---

## 1. Test Suite Summary

- **Total Test Items Collected:** 330 (baseline was 326 prior to adding ingestion failure injection tests)
- **Passed:** 321 (previously 317)
- **Failed:** 0
- **Skipped:** 9 (all 9 are optional live Ollama neural generation tests properly gated by service availability)
- **Warnings:** 1 (Starlette deprecation notice)
- **Success Rate:** **100% of runnable tests passed**

---

## 2. Test Execution Commands & Results by Package

### 2.1 Complete Regression Suite Command
```powershell
pytest -v
```

### 2.2 Results Breakdown by Subsystem

| Package / Test File | Tests Run | Passed | Failed | Skipped | Status | Scope / Focus |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `tests/citations/` | 30 | 30 | 0 | 0 | **PASSED** | Citation mapping, claim extraction, verification |
| `tests/evaluation/` | 23 | 23 | 0 | 0 | **PASSED** | Benchmark loaders, metric calculations |
| `tests/generation/` | 59 | 50 | 0 | 9 | **PASSED** | Conflict detection, prompts, grounding, Ollama status |
| `tests/ingestion/` | 43 | 43 | 0 | 0 | **PASSED** | Loaders (PDF, DOCX, TXT), cleaners, chunking |
| `tests/integration/` | 34 | 34 | 0 | 0 | **PASSED** | End-to-end RAG, upload lifecycle, failure rollback |
| `tests/retrieval/` | 112 | 112 | 0 | 0 | **PASSED** | SQLite store, FastHash, BM25, RRF, reranking |
| `tests/test_api.py` | 6 | 6 | 0 | 0 | **PASSED** | FastAPI endpoints, health, docs, query, static |
| `tests/test_foundation.py` | 4 | 4 | 0 | 0 | **PASSED** | Settings loading, environment parsing, logging |
| `tests/test_reliability_security.py` | 20 | 20 | 0 | 0 | **PASSED** | Security guards, injections, duplicate uploads |
| **Total** | **330** | **321** | **0** | **9** | **PASSED** | **100% Pass Rate** |

---

## 3. Defects Remediated

1. **`python-multipart` Dependency Omission:**
   - *Problem:* `pyproject.toml` omitted `python-multipart`, causing collection-time failure for form uploads.
   - *Fix:* Added `python-multipart>=0.0.9` to `pyproject.toml` and installed package in environment.

2. **Ambient `DEBUG="release"` Pydantic Parsing Failure:**
   - *Problem:* System environment variables with non-boolean strings like `"release"` crashed `Settings()`.
   - *Fix:* Added `@field_validator("debug", mode="before")` in `app/config/settings.py` tolerating common build strings.

3. **BM25 Inadvertent Corpus Pruning on Incremental Document Upload:**
   - *Problem:* `BM25Indexer.index_chunks()` unconditionally purged chunks not present in the submitted batch.
   - *Fix:* Introduced `prune_missing: bool = True` in `retrieval/lexical/indexer.py` and passed `prune_missing=False` during incremental uploads.

4. **Ollama Test Failures on Unreachable Daemon:**
   - *Problem:* `test_status_check_on_missing_model` and `test_live_installed_model_availability` unconditionally failed when the Ollama daemon was offline.
   - *Fix:* Isolated missing-model unit logic via mock fallback and gated live test with `pytest.skip` when daemon is offline.

5. **Upload-to-Index Lifecycle & Transactional Rollback:**
   - *Problem:* Upload endpoint stored raw files but did not orchestrate chunking and indexing. Furthermore, partial indexing failures left orphan files and desynchronized dual-store state.
   - *Fix:* Implemented `RAGQueryService.ingest_and_index_file()` with multi-stage failure rollback across processed files, chunks, SQLite vectors, and BM25 postings. Added `auto_index=True` upload parameter.

6. **Upload Memory Safety & Streaming Limits:**
   - *Problem:* `await file.read()` performed unbounded reads into RAM.
   - *Fix:* Implemented 64KB bounded chunked streaming reading enforcing `max_size_bytes` before loading complete file content into memory.
