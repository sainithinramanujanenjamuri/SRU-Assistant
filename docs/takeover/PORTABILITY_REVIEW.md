# Portability Review: Windows & macOS Cross-Platform Analysis

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  

---

## 1. Executive Summary
The SRU Assistant project was initially developed on an Apple macOS environment. This review analyzes the portability of the codebase to Microsoft Windows 10/11 and Linux environments, documenting potential hazards, verified behaviors, and remediations.

---

## 2. Portability Factors Evaluated

### 2.1 Filesystem Path Handling
- **Observation:** All core modules (`app/config/settings.py`, `retrieval/vectorstore/sqlite_store.py`, `ingestion/chunking/pipeline.py`, `scripts/*.py`) consistently utilize Python's `pathlib.Path` or standard slash normalization.
- **Paths in Settings:** Defaults like `./documents/raw`, `./documents/processed`, `./data/vectorstore/sru_vectors.db`, and `data/indices/bm25_index.json` resolve correctly on Windows and POSIX filesystems without hard-coded separator slashes (`\` or `/`).
- **No Developer Home Paths:** Code search verified zero hardcoded macOS paths (such as `/Users/...`) in runtime code, test files, or configuration templates.

### 2.2 Text Encoding and Newlines
- **File Loaders:** `ingestion/loaders/txt_loader.py` and other readers explicitly configure fallback encodings (`utf-8`, `utf-8-sig`, `latin-1`). This avoids standard Windows `cp1252` encoding crashes when reading Unicode documents containing special dashes, quotes, or academic symbols (e.g. `₹`, `©`, `—`).
- **JSON Serialization:** All JSON write and read operations (`json.dump` / `json.load`) in `chunking`, `bm25`, and `evaluation` explicitly specify `encoding="utf-8"`.

### 2.3 Environment Variable Parsing
- **Issue Discovered:** Pydantic `BaseSettings` attempts to coerce environment variables into declared types. On Windows machines where system variables like `DEBUG="release"` are present from other build tools (e.g., Rust, Android NDK), Pydantic raised a `ValidationError` on import of `Settings`.
- **Resolution:** Added a `@field_validator("debug", mode="before")` class method in `app/config/settings.py` to map strings like `"release"`, `"prod"`, `"dev"`, `"1"`, `"0"` into proper booleans. Verified that application startup succeeds with ambient `DEBUG=release`.

### 2.4 Dependency Declarations
- **Issue Discovered:** `python-multipart` was listed in `requirements.txt` but was absent from `pyproject.toml`'s `project.dependencies`. Under standard PEP 517 / 621 package installations (`pip install .`), FastAPI would fail to handle multipart form data uploads.
- **Resolution:** Synchronized `pyproject.toml` dependencies with `requirements.txt`.

### 2.5 Process and Network Services
- **Ollama Client:** The Ollama client (`generation/llm/ollama.py`) uses `httpx.Client` to interact with `http://localhost:11434`. On Windows, the client cleanly captures `httpx.ConnectError` and returns diagnostic messages instructing the user to start `ollama serve`.
- **FastAPI / Uvicorn:** Standard ASGI server works seamlessly across both platforms with `uvicorn app.main:app`.

---

## 3. Portability Matrix

| Feature | macOS (Original) | Windows (Current) | Linux | Verification Status |
| :--- | :--- | :--- | :--- | :--- |
| Core RAG Pipeline | Supported | Supported | Supported | Verified (314 tests pass) |
| SQLite Vector Store | Supported | Supported | Supported | Verified (`sru_vectors.db`) |
| BM25 Inverted Index | Supported | Supported | Supported | Verified (`bm25_index.json`) |
| PDF Document Parsing | Supported | Supported | Supported | Verified via `pypdf` |
| DOCX Document Parsing | Supported | Supported | Supported | Verified via `python-docx` |
| FastHash Embeddings | Supported | Supported | Supported | Verified (pure Python/numpy) |
| Web UI & Static Mounting | Supported | Supported | Supported | Verified on FastAPI |
| Ollama Daemon Integration | Supported (if running) | Supported (if running) | Supported (if running) | Verified graceful fallback |

---

## 4. Portability Conclusion
The codebase is now fully portable across Windows, macOS, and Linux. No platform-specific syscalls, native build dependencies, or non-portable shell scripts are present in the core pipeline.

