# Generation, Grounding, and Citation Validation

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  
**Scope:** Answer Synthesis, Grounded Prompting, Conflict Detection, N-Gram Grounding Validation, Inline Citation Mapping, and Support Verification  

---

## 1. Generation Pipeline Architecture

The generation layer synthesizes university query answers strictly anchored in retrieved evidence:

```
[Retrieved Candidate Chunks]
               │
               ▼
       [ContextBuilder]       ──► Bounds tokens to rag_context_max_tokens (1500), adds <evidence id='X'> tags
               │
               ▼
      [ConflictDetector]      ──► Scans evidence across sources for dates, regulation, or credit contradictions
               │
               ▼
   [GroundedPromptTemplate]   ──► Injects strict system prompt ("Rely solely on provided evidence. Do not extrapolate.")
               │
               ▼
     [LLM / Generator]        ──► Deterministic baseline or local Ollama client (qwen2.5 / qwen3.5)
               │
               ▼
     [ClaimExtractor]         ──► Extracts discrete factual assertions from generated text
               │
               ▼
    [GroundingValidator]      ──► Computes token overlap & n-gram containment against context
               │
               ▼
     [CitationVerifier]       ──► Maps inline bracket citations [1], [2] to chunks, scores support, flags unverified
               │
               ▼
       [QueryResponse]        ──► Returns cited_answer, citations, verification summary, and telemetry
```

---

## 2. Evaluation of 8 Required Architectural Scenarios

| Scenario | System Behavior & Defense Mechanism | Verification Status & Test Evidence |
| :--- | :--- | :--- |
| **Scenario A: Answer exists clearly in one source** | Retrieved chunk provides exact match. Generator synthesizes factual answer with inline citation `[1]`. `CitationVerifier` validates support score $\ge 0.7$, `citation_precision = 1.0`. | **Verified.** `tests/integration/test_baseline_rag_integration.py` & `tests/test_api.py::test_api_query_grounded_answer`. |
| **Scenario B: Question requires paraphrase matching** | Hybrid dense FastHash matching captures semantic intent despite lexical variance. Evidence is retrieved and answered with verified citation. | **Verified.** `tests/retrieval/test_benchmark.py::test_paraphrased_semantic_query`. |
| **Scenario C: Answer requires evidence from multiple documents** | `ContextBuilder` aggregates chunks from distinct source documents (e.g. syllabus + calendar). Multi-source synthesis generates combined answer citing both sources `[1], [2]`. | **Verified.** `tests/generation/test_multi_document_synthesis.py::test_multi_source_aggregation`. |
| **Scenario D: Conflicting information across sources** | `ConflictDetector` analyzes dates, semester timelines, and regulation versions across retrieved chunks. If discrepancy is found, emits `ConflictReport(has_conflict=True)` with conflicting sources and flags `has_conflicts=True` in API response. | **Verified.** `tests/generation/test_conflict_detector.py` (7 tests pass). |
| **Scenario E: No available document supports the answer** | If retrieved chunks fail relevance threshold or do not contain facts, system outputs `INSUFFICIENT_EVIDENCE_FALLBACK` ("Based on the available SR University documentation, there is insufficient information..."), returning zero hallucinated claims and zero false citations. | **Verified.** `tests/test_api.py::test_api_query_safe_refusal` & `tests/generation/test_grounding_validator.py`. |
| **Scenario F: Generator or external provider is unavailable** | If configured provider is unreachable (e.g. Ollama daemon offline), `is_available()` returns `False` with actionable instructions (`ollama serve`). Direct generation calls raise `LLMProviderUnavailableError` without crashing the process. | **Verified.** `tests/generation/test_generators.py::test_status_check_on_unreachable_server` & `test_connection_error_raises_llm_provider_unavailable`. |
| **Scenario G: Generated answer contains claim unsupported by evidence** | `ClaimExtractor` isolates candidate sentences. `GroundingValidator` calculates n-gram overlap against context. Any statement below `grounding_min_token_overlap` (0.4) is marked unsupported, triggering `is_grounded = False` or strict fallback. | **Verified.** `tests/generation/test_grounding_validator.py` (10 tests pass). |
| **Scenario H: Citation points to incorrect source or page** | `CitationVerifier` compares extracted claim against the specific text of the cited chunk. If entity or token overlap is insufficient, `is_verified` is set to `False` and `unsupported_claims_count` is incremented. | **Verified.** `tests/citations/test_citation_verifier.py` (5 tests pass). |

---

## 3. Provider Adapters & Offline Repeatability

1. **Deterministic Baseline Generator (`generation/llm/deterministic.py`):**
   - Active default in `.env` (`LLM_PROVIDER=deterministic`).
   - Pure Python rule-based extractor that scans `<evidence>` blocks for sentences matching the question's key academic entities (dates, course numbers, credits).
   - Produces 100% deterministic, repeatable outputs in $< 5\text{ ms}$ without GPU or network access.

2. **Ollama Neural Client (`generation/llm/ollama.py`):**
   - Communicates via HTTP with local Ollama service (`/api/generate` and `/api/tags`).
   - Supports parameter tuning: `temperature=0.0`, `max_tokens=512`, `top_p`.
   - Distinguishes daemon unreachable errors (`httpx.ConnectError`) from missing model errors (`"not pulled"`).
   - Live neural tests skip cleanly when daemon is not running, preserving deterministic test suite health.

---

## 4. Citation and Provenance Traceability
Every citation emitted in `QueryResponse.citations` contains complete provenance:
- `citation_id`: Sequential bracket identifier (`[1]`, `[2]`).
- `document_name`: Source file name (e.g. `sru_academic_calendar_2026_27.txt`).
- `page` / `page_info`: Page number or line range.
- `section`: Hierarchical heading section.
- `chunk_id`: Deterministic unique identifier linking back to SQLite vector database and BM25 index.
- `claim_text`: The exact sentence making the assertion.
- `is_verified`: Boolean validation status.
- `support_score`: Float support confidence score.

