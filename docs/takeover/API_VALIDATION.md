# Backend and API Integration Validation

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  
**Framework:** FastAPI 0.115+, Uvicorn 0.34+, Pydantic v2  

---

## 1. REST Endpoint Specifications & Contracts

The application layer exposes RESTful endpoints under `/api` alongside static web routes:

### 1.1 `GET /api/health`
- **Purpose:** System operational telemetry, LLM provider availability, and index statistics.
- **Response Schema (`HealthResponse`):**
  ```json
  {
    "status": "healthy",
    "app_name": "SRU Assistant",
    "version": "1.0.0",
    "llm_provider": "deterministic",
    "llm_model": "qwen3.5:0.8b",
    "llm_available": true,
    "llm_status_message": "Available",
    "embedding_provider": "fasthash",
    "vectorstore_records": 21,
    "bm25_indexed": true
  }
  ```

### 1.2 `POST /api/query`
- **Purpose:** Grounded academic question resolution.
- **Request Schema (`QueryRequest`):**
  - `query`: string (min length 2, max length 1000).
  - `top_k`: integer (default 5, range 1-20).
  - `retrieval_mode`: string (`"dense"`, `"lexical"`, `"hybrid"`, `"enhanced"`).
  - `verify_citations`: boolean (default true).
  - `citation_style`: string (`"inline_bracket"`, `"source_block"`, `"footnote"`).
- **Response Schema (`QueryResponse`):**
  - `request_id`: UUID-based tracking identifier (e.g. `req_a1b2c3d4e5f60718`).
  - `query`: normalized question string.
  - `answer`: synthesized answer text.
  - `cited_answer`: answer string formatted with inline citation brackets `[1]`.
  - `citations`: list of `CitationDetail` records with source, page, chunk_id, and claim.
  - `verification`: `VerificationSummary` with precision, recall, and support score.
  - `is_grounded`: boolean flag indicating zero ungrounded assertions.
  - `has_conflicts`: boolean flag indicating whether source contradictions were detected.
  - `latency_ms`: latency breakdown (retrieval, context, conflict, generation, grounding, citation, total).
  - `engine_info`: execution metadata.

### 1.3 `POST /api/documents/upload`
- **Purpose:** Document upload with security inspection and optional automated indexing.
- **Parameters:**
  - `file`: Multipart form file (`.pdf`, `.docx`, `.txt`).
  - `auto_index`: Optional boolean query parameter (default `false`). When `true`, automatically parses, chunks, and indexes the document into SQLite vector and BM25 stores.
- **Response Schema (`DocumentUploadResponse`):**
  - `filename`: sanitized filename.
  - `status`: `"uploaded"`, `"indexed"`, or `"duplicate"`.
  - `file_size_bytes`: integer size in bytes.
  - `sha256_hash`: hex content hash.
  - `is_duplicate`: boolean flag.
  - `message`: human-readable status description.

### 1.4 `GET /api/documents`
- **Purpose:** Catalog of indexed institutional documents.
- **Response Schema:** Array of `DocumentSummary` objects containing `document_id`, `document_name`, `document_type`, `category`, `academic_year`, `chunk_count`, and `source_file`.

### 1.5 Web & Documentation Routes
- `GET /`: Serves `frontend/index.html` (Interactive Academic Query Portal).
- `GET /presentation`: Serves `frontend/presentation.html` (Interactive Capstone Viva Slides).
- `GET /docs`: Swagger UI OpenAPI interactive documentation.
- `GET /redoc`: ReDoc API documentation.

---

## 2. Status Code & Error Handling Matrix

| Condition | Status Code | Error Response Pattern |
| :--- | :--- | :--- |
| Valid Query Resolution | `200 OK` | Full `QueryResponse` with verified citations |
| Prompt Injection Attempt | `200 OK` | Controlled refusal answer with security threat code and `request_id` |
| Empty / Whitespace Query | `422 Unprocessable Entity` | Pydantic validation error or `QuerySecurityError` |
| Disallowed File Upload (.exe, .sh) | `400 Bad Request` | `{"detail": "File extension '.exe' is not permitted"}` |
| Corrupted File Header | `400 Bad Request` | `{"detail": "Corrupted or invalid PDF header"}` |
| File Size Exceeds 15MB Limit | `400 Bad Request` | `{"detail": "File size exceeds maximum permitted limit"}` |
| Unhandled Internal Exception | `500 Internal Server Error` | Clean error envelope without leaking server internals or traces |

---

## 3. Telemetry & Request Tracking
Every API query is assigned a cryptographically randomized 16-character `request_id` (`req_...`) logged via `ObservabilityLogger`. The telemetry record captures:
- Request ID and timestamp.
- Query character length.
- Latency breakdown across each RAG stage (retrieval, context, conflict, generation, grounding, citation).
- Retrieved documents and citation counts.
- Threat classification if security guard triggered.
- HTTP status code.

