# Initial Audit: SRU Assistant Capstone Project

**Date:** 2026-11-05  
**Auditor:** Senior AI & Software Engineer (Takeover Lead)  
**Project:** SRU Assistant — A RAG Framework for University Academic Query Resolution  

---

## 1. Executive Status Classification

| Category | Component / Feature | Current State | Verification Evidence / Details |
| :--- | :--- | :--- | :--- |
| **Implemented & Verified** | Ingestion & Document Loaders | **Verified** | Parsers for TXT, DOCX, and PDF pass all unit tests in `tests/ingestion/test_loaders.py`. |
| **Implemented & Verified** | Structure-Aware Chunking | **Verified** | Tokenizer, heading preservation, table detection, and chunk overlap pass all tests in `tests/ingestion/test_chunking.py`. |
| **Implemented & Verified** | BM25 Lexical Index & Retriever | **Verified** | Academic tokenizer, inverted index persistence, and BM25 ranking pass all tests in `tests/retrieval/test_bm25.py`. Index present at `data/indices/bm25_index.json`. |
| **Implemented & Verified** | SQLite Vector Store & FastHash | **Verified** | Blob float32 vector storage, cosine similarity retrieval, and deterministic fasthash embeddings pass in `tests/retrieval/test_vectorstore.py` and `tests/retrieval/test_embeddings.py`. Database present at `data/vectorstore/sru_vectors.db`. |
| **Implemented & Verified** | Hybrid Retrieval & RRF Fusion | **Verified** | Reciprocal Rank Fusion of dense and lexical candidates passes all tests in `tests/retrieval/test_fusion.py` and `tests/retrieval/test_hybrid_retriever.py`. |
| **Implemented & Verified** | Metadata Filtering & Reranking | **Verified** | Query analyzer, metadata filter, and deterministic reranker pass in `tests/retrieval/test_rerankers.py` and `tests/retrieval/test_metadata_filter.py`. |
| **Implemented & Verified** | Grounding & Conflict Detection | **Verified** | N-gram token overlap validator, strict grounding refusal, and cross-source conflict detection pass in `tests/generation/test_grounding_validator.py` and `tests/generation/test_conflict_detector.py`. |
| **Implemented & Verified** | Citation Verification & Mapping | **Verified** | Sentence claim extraction, bracket mapping, and chunk support scoring pass in `tests/citations/`. |
| **Implemented & Verified** | Deterministic Generation Baseline | **Verified** | Offline reproducible testing passes without requiring external API or GPU. |
| **Implemented & Verified** | Security Guards & Telemetry | **Verified** | Prompt injection protection, malicious extension/magic byte checking, sha256 deduplication, and structured telemetry logging pass in `tests/test_reliability_security.py`. |
| **Implemented & Verified** | FastAPI REST Endpoints | **Verified** | Endpoints `/api/health`, `/api/query`, `/api/documents`, and `/api/documents/upload` pass tests in `tests/test_api.py`. |
| **Implemented & Verified** | Frontend Web Interface | **Verified** | Static files (`index.html`, `presentation.html`, `app.js`, `styles.css`) mounted and served via FastAPI. |
| **Broken (Genuine Defect)** | Unit Test Ollama Assumptions | **Broken** | `tests/generation/test_generators.py` had 2 unit tests asserting that an Ollama daemon is running with `qwen2.5:0.5b` installed on `localhost:11434`. Unit tests should not unconditionally fail when an optional external daemon is offline. |
| **Partially Implemented** | Upload-to-Index Orchestration | **Partial** | File upload endpoint validates and stores raw documents into `documents/raw/`, but does not automatically trigger parsing, chunking, and incremental vector/BM25 indexing in the active session. |
| **Partially Implemented** | Environment Portability | **Partial** | Pydantic `Settings.debug` failed when OS environment variable `DEBUG` was set to `"release"`. `python-multipart` was declared in `requirements.txt` but omitted in `pyproject.toml`. |
| **Blocked by Environment** | Live Neural Ollama Generation | **Blocked** | Ollama binary is installed (`ollama.exe`), but the background daemon is not running on port 11434 in the test environment. Live neural tests properly skip. |

---

## 2. In-Depth Component Analysis

### 2.1 Dependencies and Build System
- `requirements.txt` specifies minimum dependencies: Pydantic, pydantic-settings, python-dotenv, pypdf, python-docx, numpy, httpx, fastapi, uvicorn, python-multipart, pytest, and ruff.
- `pyproject.toml` declared dependencies, but previously omitted `python-multipart`. This has been identified and will be synchronized.

### 2.2 Environment and Configuration Portability
- `app/config/settings.py` loads from `.env` and system environment variables.
- The `debug: bool` field fails to parse common non-boolean environment values such as `"release"`. A field validator is required to make the configuration resilient across developer machines.
- All file paths in settings use relative paths (`./documents/raw`, `./data/vectorstore/sru_vectors.db`, `data/indices/bm25_index.json`), which resolves cleanly on both Windows and macOS/Linux.

### 2.3 Document Ingestion Pipeline
- Supports `.pdf`, `.docx`, and `.txt` files.
- Uses `DocumentCleaner` to strip repeating running headers and footers across pages.
- `StructureAwareChunker` preserves headings, document sections, and table formats.
- Every chunk includes metadata (document name, academic year, category, semester) and provenance (file name, page numbers, character offsets, hash).

### 2.4 Retrieval Architecture
- **Dense Vector Store:** Uses SQLite (`data/vectorstore/sru_vectors.db`) storing float32 blob embeddings. FastHash produces deterministic 384-dimensional embeddings for local CPU execution.
- **Lexical Index:** Custom BM25 implementation with academic tokenizer (handling terms like CSE-401, R23, SGPA, CGPA). Index stored in `data/indices/bm25_index.json`.
- **Hybrid Retrieval:** Reciprocal Rank Fusion (`retrieval/fusion/rrf.py`) with configurable constant $k=60$.
- **Reranker:** Lexical and entity match reranker (`retrieval/reranking/deterministic.py`).

### 2.5 Generation, Grounding, and Citations
- Uses `ContextBuilder` with token caps to avoid context overflow.
- Strict system prompt requires answers to rely solely on context.
- `GroundingValidator` computes token and n-gram overlap between generated claims and retrieved context chunks.
- If no context chunks exceed the relevance threshold or no evidence supports the query, returns institutional refusal rather than hallucinating.
- `CitationVerifier` validates every inline citation `[1]`, `[2]` against the source chunk text.

### 2.6 Security & Guardrails
- `QueryGuard`: Regex and keyword detection for prompt injection patterns ("ignore previous instructions", "jailbreak", "system override"), query length limits (2 to 1000 chars).
- `DocumentGuard`: Magic bytes validation (PDF, DOCX ZIP signature, valid UTF text), file size limits (max 15MB), SHA-256 deduplication, and filename path traversal sanitization.
- `Telemetry`: Request ID tracking, latency breakdowns, and structured logging.

---

## 3. Required Remediation Actions
1. **Settings Resiliency:** Add validator in `app/config/settings.py` for `debug` to gracefully parse non-boolean strings like `"release"`, `"prod"`, `"dev"`.
2. **Synchronize Dependencies:** Update `pyproject.toml` to include `python-multipart`.
3. **Fix Ollama Unit Tests:** Update `tests/generation/test_generators.py` so unit tests mock the HTTP responses or properly check daemon status, preventing failure when the external service is offline.
4. **End-to-End Upload Lifecycle:** Add orchestration method in `RAGQueryService` to allow indexing newly uploaded documents so they become immediately searchable.
5. **Execute Benchmarks & E2E Demo:** Validate all benchmarks and verify end-to-end functionality via CLI and API.

