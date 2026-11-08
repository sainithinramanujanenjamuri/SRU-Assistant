# Phase 11: Reliability & Security Layer

## 1. Phase Status
- **Status**: COMPLETED
- **Completed Date**: October 2026
- **Test Coverage**: 20 dedicated tests in `tests/test_reliability_security.py` (309 total tests passing in project)

## 2. Objective
Make the SRU Assistant framework robust, secure, and ready for production viva demonstration by providing:
1. **Query Safety**: Length bounding, input sanitization, prompt injection defense, and jailbreak neutralization.
2. **Document Security**: File validation, size limits, allowed format whitelisting, duplicate detection via SHA-256 fingerprinting, and path traversal protection.
3. **Observability & Telemetry**: Unique request tracing (`request_id`), performance timing breakdown, and privacy-preserving audit logging.
4. **Zero-Hallucination Safe Refusals**: Strict evidence-grounded refusal mechanics for unsupported or malicious queries.

## 3. Architecture & Components
Located in `app/security/`:
- `query_guard.py`:
  - `QueryGuard`: Inspects raw user queries. Enforces minimum (2) and maximum (1000) character constraints, strips malicious HTML/scripts and control characters.
  - Detects prompt injection signatures (`ignore previous instructions`, `DAN mode`, `system prompt override`, `jailbreak`, etc.).
  - Returns `QueryGuardResult` with calibrated university refusal text: *"I am SRU Assistant, an academic query resolution framework for SR University..."*
- `document_guard.py`:
  - `DocumentGuard`: Sanitizes uploaded filenames, neutralizing directory traversal sequences (`../../`, `..\\`).
  - Validates file format against whitelist (`.pdf`, `.docx`, `.txt`).
  - Checks magic header signatures (`%PDF-`, `PK\x03\x04`).
  - Computes SHA-256 hashes to detect duplicate documents.
  - Enforces file size boundaries (10 bytes min, 25MB max).
- `telemetry.py`:
  - `generate_request_id()`: Creates unique per-query request identifiers (`req_<hex>`).
  - `RequestTelemetry`: Captures execution metrics (`latency_breakdown_ms`, `retrieval_count`, `retrieved_documents`, `citation_count`, `is_grounded`, `status_code`, `threat_detected`).
  - `ObservabilityLogger`: Emits structured operational logs while omitting raw student question text to protect user privacy.

## 4. API Endpoints Enhanced
- `POST /api/query`:
  - Returns `request_id` in response payload.
  - Runs query through `QueryGuard`. If prompt injection is detected, logs threat and returns safe refusal response in 0.2ms.
  - Returns HTTP 422 on empty or out-of-boundary queries.
- `POST /api/documents/upload`:
  - Accepts multipart form uploads (`UploadFile`).
  - Enforces `DocumentGuard` security policies.
  - Returns HTTP 400 for forbidden extensions or corrupted headers.
  - Detects duplicate files with `status: "duplicate"`.

## 5. Verification & Test Suite
- `tests/test_reliability_security.py`:
  - 20 automated unit and integration tests covering:
    - Normal query acceptance
    - Empty and whitespace-only rejection
    - Min and max length boundary enforcement
    - Script tag and control character sanitization
    - Prompt injection detection across 5 distinct jailbreak patterns
    - Path traversal neutralization in filenames
    - Plain text, docx, and corrupted PDF header validation
    - Duplicate detection by hash
    - Request ID format and telemetry serialization
    - Live API query prompt injection refusal
    - Live API document upload and duplicate flow
- Entire repository test suite: **309 passed in 1.03s**.
