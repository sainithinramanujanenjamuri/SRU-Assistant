# End-to-End Demonstration Guide & Execution Log

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  
**Demonstration Scope:** 13 Step-by-Step Scenarios from Application Launch to Live Upload & Query Resolution  

---

## 1. Step 1: Start the Application

Execute the Uvicorn ASGI server from the project root:
```powershell
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
Expected output:
```
INFO:     Started server process [PID]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 2. Step 2: Check System Health

**HTTP Request:**
```http
GET /api/health HTTP/1.1
Host: localhost:8000
```
**Observed Response:**
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
**Outcome:** System operational; SQLite vector store and BM25 index confirmed loaded.

---

## 3. Step 3: Inspect Indexed Institutional Documents

**HTTP Request:**
```http
GET /api/documents HTTP/1.1
Host: localhost:8000
```
**Observed Response:**
```json
[
  {
    "document_id": "doc_calendar_2026_27",
    "document_name": "sru_academic_calendar_2026_27.txt",
    "document_type": ".txt",
    "category": "academic_calendar",
    "academic_year": "2026-27",
    "chunk_count": 1,
    "source_file": "sru_academic_calendar_2026_27.txt"
  },
  {
    "document_id": "doc_syllabus_23cse302t",
    "document_name": "sru_btech_cse_syllabus_sem7.txt",
    "document_type": ".txt",
    "category": "syllabus",
    "academic_year": "2026-27",
    "chunk_count": 2,
    "source_file": "sru_btech_cse_syllabus_sem7.txt"
  }
]
```

---

## 4. Step 4 to 7: Known-Answer Query, Evidence, Answer, and Citation

**HTTP Request:**
```http
POST /api/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "When is Mid-Semester Examination I scheduled for B.Tech VII Semester?",
  "top_k": 5,
  "retrieval_mode": "enhanced",
  "verify_citations": true
}
```
**Observed Response:**
```json
{
  "request_id": "req_88a2efc4091a",
  "query": "When is Mid-Semester Examination I scheduled for B.Tech VII Semester?",
  "answer": "Based on the official SR University documentation, Mid-Semester Examination I is scheduled on 12 September 2026.",
  "cited_answer": "Based on the official SR University documentation, Mid-Semester Examination I is scheduled on 12 September 2026 [1].",
  "citations": [
    {
      "citation_id": "1",
      "document_name": "sru_academic_calendar_2026_27.txt",
      "page": null,
      "page_info": "Line 4-12",
      "section": "Academic Calendar > Examination Schedule",
      "source_label": "doc_calendar_2026_27_chunk_0000",
      "chunk_id": "doc_calendar_2026_27_chunk_0000",
      "claim_text": "Mid-Semester Examination I is scheduled on 12 September 2026.",
      "is_verified": true,
      "support_score": 1.0
    }
  ],
  "verification": {
    "is_fully_supported": true,
    "citation_precision": 1.0,
    "citation_recall": 1.0,
    "overall_support_score": 1.0,
    "unsupported_claims_count": 0
  },
  "is_grounded": true,
  "has_conflicts": false,
  "latency_ms": {
    "retrieval": 1.15,
    "context": 0.18,
    "conflict": 0.09,
    "generation": 0.82,
    "grounding": 0.35,
    "citation": 0.41,
    "total": 3.0
  }
}
```
**Outcome:** Answer retrieved in 3.0ms with exact date `12 September 2026`, verified citation `[1]`, and 100% grounding.

---

## 5. Step 8: Keyword Lookup (Course Code `23CSE302T`)

**HTTP Request:**
```http
POST /api/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "What are the core units covered in 23CSE302T?",
  "top_k": 3,
  "retrieval_mode": "enhanced"
}
```
**Outcome:** BM25 academic tokenizer captures alphanumeric code `23CSE302T`. Retrieves syllabus chunk covering Machine Learning and Deep Learning units.

---

## 6. Step 9: Paraphrased Query

**HTTP Request:**
```http
POST /api/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "At what point in the semester do VII sem students take their initial midterms?",
  "top_k": 5,
  "retrieval_mode": "enhanced"
}
```
**Outcome:** Dense FastHash matching successfully bridges lexical divergence ("take their initial midterms" $\rightarrow$ "Mid-Semester Examination I"), retrieving the correct examination date.

---

## 7. Step 10: Unsupported Out-of-Domain Question

**HTTP Request:**
```http
POST /api/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "What are the campus parking fees and permits for two-wheelers?",
  "top_k": 5
}
```
**Observed Response:**
```json
{
  "answer": "Based on the available SR University documentation, there is insufficient information to answer this question. Please consult official university notifications or academic administration.",
  "citations": [],
  "is_grounded": true,
  "verification": {
    "is_fully_supported": true,
    "unsupported_claims_count": 0
  }
}
```
**Outcome:** Controlled zero-hallucination refusal. No unsupported assertions made.

---

## 8. Step 11: Controlled Failure Handling on Offline Provider

**Configuration Check:**
When configured with an offline endpoint (`http://localhost:59999`):
```python
client = OllamaLLMClient(base_url="http://localhost:59999")
available, msg = client.is_available()
```
**Observed Result:** `available = False`, `msg = "Cannot connect to Ollama daemon at http://localhost:59999. Please ensure Ollama is running (e.g. 'ollama serve')."`  
**Outcome:** Clean diagnostic message without uncaught socket crashes.

---

## 9. Step 12 & 13: Live Document Upload & Immediate Query

**Step 12: Upload New Circular with `auto_index=true`**
```bash
curl -X POST "http://localhost:8000/api/documents/upload?auto_index=true" \
  -F "file=@sru_quantum_circular_2026.txt"
```
**Observed Response:**
```json
{
  "filename": "sru_quantum_circular_2026.txt",
  "status": "indexed",
  "file_size_bytes": 368,
  "sha256_hash": "2213012d42a76f17...",
  "is_duplicate": false,
  "message": "Document 'sru_quantum_circular_2026.txt' successfully processed, chunked (1 chunks), and indexed into vector and BM25 stores."
}
```

**Step 13: Query Newly Indexed Content**
```http
POST /api/query HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "query": "What is the prerequisite for Quantum Computing course 23QNT401T?"
}
```
**Observed Response:**
```json
{
  "answer": "Based on the official SR University documentation, the newly approved prerequisite for Quantum Computing is Advanced Linear Algebra with minimum grade B+.",
  "cited_answer": "Based on the official SR University documentation, the newly approved prerequisite for Quantum Computing is Advanced Linear Algebra with minimum grade B+ [1].",
  "citations": [
    {
      "citation_id": "1",
      "document_name": "sru_quantum_circular_2026.txt",
      "is_verified": true
    }
  ]
}
```
**Outcome:** Verified end-to-end. Newly uploaded content is immediately searchable and verifiable.

