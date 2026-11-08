# Phase 5 — Hybrid Retrieval: Completion Report

**Project**: SRU Assistant: A RAG Framework for University Academic Query Resolution  
**Phase**: Phase 5 — Hybrid Retrieval (BM25 + Dense Fusion)  
**Status**: COMPLETE & VERIFIED  
**Date**: 2026-09-17  

---

## 1. Executive Summary

Phase 5 established the **Hybrid Retrieval** layer for SRU Assistant, unifying dense semantic vector search (Phase 3) with sparse lexical search (BM25) through formal candidate fusion algorithms. In strict compliance with `roadmap.md` (lines 489–544), `RAG.md` (lines 430–526), `framework.md` (lines 345–360), `agent.md` (lines 397–416), and all 23 Phase 5 Engineering Amendments, Phase 5 implements:

1. **Academic-Aware Lexical Tokenizer (`AcademicLexicalTokenizer`)**:
   - Preserves institutional tokens intact: course codes (e.g. `23CSE302T`), regulation identifiers (`R23`), academic sessions (`2026-27`), dates (`12 September 2026`), and acronyms (`CSE`, `B.Tech`).
   - Suffix normalization handles regular English plurals (`examinations` $\to$ `examination`, `algorithms` $\to$ `algorithm`) while protecting Latin root nouns (`syllabus`, `campus`, `status`, `analysis`) and alphanumeric codes.
   - Preserves both composite hyphenated tokens and constituent subparts (`mid-semester`, `mid`, `semester`).
2. **Mathematically Rigorous BM25 Subsystem (`BM25Index`, `BM25Retriever`, `BM25Indexer`)**:
   - BM25Okapi scoring with Robertson/Spärck Jones non-negative IDF: $\text{IDF}(t) = \ln\left(\frac{N - \text{df}(t) + 0.5}{\text{df}(t) + 0.5} + 1\right)$.
   - Configurable parameters: $k_1 = 1.5, b = 0.75$.
   - Content-hash delta indexing tracking `SHA-256(chunk.text)` across 4 lifecycle states: `UNCHANGED`, `MODIFIED`, `NEW`, and `REMOVED`.
   - Index manifest (`BM25IndexManifest`) verifying runtime compatibility (`IndexCompatibilityError`).
   - Metadata pre-filtering matching Phase 3 schema (`department`, `semester`, `regulation`, `academic_year`, `document_type`).
   - Deterministic tie-breaking: `bm25_score` DESC, `chunk_id` ASC.
3. **Decoupled Multi-Channel Fusion Engines**:
   - **Reciprocal Rank Fusion (`ReciprocalRankFusion`)**: Standard RRF with $k=60$ and modality weights ($w_d=1.0, w_l=1.0$). Strictly documented as a rank aggregation metric, not a calibrated probability.
   - **Weighted Score Fusion (`WeightedScoreFusion`)**: Convex linear combination $\alpha \cdot \text{dense} + (1-\alpha) \cdot \text{lexical}$ with $\alpha=0.50$ ($0 \le \alpha \le 1$). Initial heuristic awaiting Phase 9 tuning.
   - Missing modality handling: missing candidate receives rank `None` and score contribution $0.0$.
4. **Hybrid Retriever Coordinator (`HybridRetriever`)**:
   - Candidate pool expansion: retrieves larger pools from dense and lexical channels (`dense_candidate_k=20`, `lexical_candidate_k=20`) before fusion into `final_top_k=5`.
   - Explicit channel failure semantics (Cases A through E) with configurable fallback (`allow_channel_fallback=False`).
   - Multi-mode support: `hybrid` (fused), `dense` (vector only), or `lexical` (BM25 only).
   - Observability metadata (`HybridRetrievalMeta`) tracking per-channel latencies and hit counts.
5. **Decoupled Protocol & RAG Integration**:
   - `BaseRetriever(Protocol)` declaring `search(query, top_k, filters)`.
   - `BaselineRAGPipeline` updated to operate seamlessly with `VectorRetriever`, `BM25Retriever`, or `HybridRetriever`.
   - `RAGResponse` enriched with `retrieval_mode` and `hybrid_meta` diagnostics.
6. **CLI Utilities & Preliminary Benchmark**:
   - `scripts/build_bm25_index.py`: Batch and delta indexer with `--force-rebuild`.
   - `scripts/search_hybrid.py`: Side-by-side retrieval diagnostic tool.
   - `scripts/rag_query.py`: Enriched with `--retrieval-mode` and `--fusion-method`.
   - `retrieval/hybrid_benchmark.py`: Empirical evaluation across 5 academic query categories.

---

## 2. Architecture & Design Decisions

### 2.1 BM25 Mathematical Formulation (Amendment 1)
BM25Okapi scoring is implemented as:
$$\text{IDF}(t) = \ln\left(\frac{N - \text{df}(t) + 0.5}{\text{df}(t) + 0.5} + 1\right)$$
$$\text{BM25}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \cdot \frac{\text{tf}(t, D) \cdot (k_1 + 1)}{\text{tf}(t, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
The $+1.0$ term inside the logarithm ensures IDF is strictly non-negative ($\text{IDF} > 0.0$) for all $\text{df} \le N$, preventing negative score distortions for terms appearing in all documents.

### 2.2 Content-Hash Delta Indexing (Amendment 3)
Freshness is determined exclusively by `SHA-256(chunk.text)`:
- `UNCHANGED`: matching `chunk_id` and hash $\to$ skipped.
- `MODIFIED`: matching `chunk_id` and differing hash $\to$ postings and doc length updated.
- `NEW`: new `chunk_id` $\to$ indexed and added.
- `REMOVED`: existing chunk missing from submission $\to$ postings pruned.

### 2.3 Manifest & Compatibility Enforcement (Amendment 4)
Manifest schema (`BM25IndexManifest`):
```json
{
  "index_version": "1.0.0",
  "tokenizer_version": "1.0.0",
  "vocabulary_size": 51,
  "total_chunks": 3,
  "average_document_length": 22.33,
  "k1": 1.5,
  "b": 0.75,
  "created_at": "2026-09-17T02:37:44.123456+00:00",
  "source_content_hash": "..."
}
```
Any mismatch in `tokenizer_version`, `k1`, or `b` raises `IndexCompatibilityError`, requiring explicit `--force-rebuild`.

### 2.4 Metadata Filtering (Amendment 5)
Logically equivalent pre-filtering is applied to both channels before ranking:
`department`, `semester`, `regulation`, `academic_year`, `document_type`.
Neither channel bypasses metadata filters.

### 2.5 Score Normalization & RRF Calibration Status (Amendments 6, 7, 8)
- BM25 normalized score: Min-max scaled per query into $[0.0, 1.0]$. When all scores are identical, normalized score evaluates deterministically to $1.0$.
- RRF: $k=60$. Display score normalized by theoretical max. Documented: **not a probability or calibrated similarity score**.
- Weighted fusion: $\alpha = 0.50$. Documented: **initial heuristic, not an optimal bound**; subject to Phase 9 tuning.

### 2.6 Candidate Pooling vs Top-K (Amendment 13)
Candidate pool parameters:
- `dense_candidate_k = 20`
- `lexical_candidate_k = 20`
- `final_top_k = 5`
This enables fusion algorithms to recover documents that one channel ranks moderately lower.

### 2.7 Channel Failure Semantics (Amendment 10)
- **Case A** (Both work): Normal fusion.
- **Case B** (Dense fails, BM25 works): Fallback to BM25 if `allow_channel_fallback=True` (`mode="lexical_fallback"`), else raises `RetrievalError`.
- **Case C** (BM25 fails, Dense works): Fallback to Dense if `allow_channel_fallback=True` (`mode="dense_fallback"`), else raises `RetrievalError`.
- **Case D** (Both fail): Strictly raises `RetrievalError`.
- **Case E** (Both 0 results): Returns empty list `[]` (normal no-evidence state, short-circuits to fallback).

### 2.8 Deterministic Tie-Breaking (Amendment 14)
- BM25: `bm25_score` DESC, `chunk_id` ASC.
- RRF: `fused_score` DESC, `chunk_id` ASC.
- Weighted: `fused_score` DESC, `chunk_id` ASC.

---

## 3. Empirical Benchmarks & Measured Metrics

Per Amendments 16, 17, and 18, comparative benchmarks were executed on the active system using the 5 academic query categories from `roadmap.md` over the Phase 3 synthetic evaluation set:

```bash
python -m retrieval.hybrid_benchmark
```

### 3.1 Comparative Retrieval Evaluation

| Retrieval Method | Recall@1 | Recall@3 | MRR | Mean Latency |
|---|---|---|---|---|
| **Dense Only (FastHash)** | 1.0000 | 1.0000 | 1.0000 | 0.42 ms |
| **BM25 Only** | 1.0000 | 1.0000 | 1.0000 | 0.06 ms |
| **Hybrid (RRF k=60)** | 1.0000 | 1.0000 | 1.0000 | 1.15 ms |
| **Hybrid (Weighted $\alpha=0.5$)** | 1.0000 | 1.0000 | 1.0000 | 0.55 ms |

### 3.2 Per-Query Latency & Resolution Breakdown

| Category | Query | Dense Latency | BM25 Latency | Hybrid RRF | Hybrid Weighted | Status |
|---|---|---|---|---|---|---|
| **Semantic Concept** | *"Which tree structures and graph algorithms are taught?"* | 0.57 ms | 0.13 ms | 3.81 ms | 0.71 ms | HIT |
| **Course Code** | *"23CSE302T course syllabus"* | 0.30 ms | 0.04 ms | 0.45 ms | 0.47 ms | HIT |
| **Date** | *"12 September 2026 examination schedule"* | 0.28 ms | 0.06 ms | 0.49 ms | 0.52 ms | HIT |
| **Regulation** | *"Regulation R23 attendance rules"* | 0.26 ms | 0.04 ms | 0.45 ms | 0.41 ms | HIT |
| **Exact Term** | *"Dussehra vacation academic calendar"* | 0.67 ms | 0.04 ms | 0.53 ms | 0.63 ms | HIT |

*(Note: Explicitly labeled: Preliminary Phase 5 Retrieval Comparison. Formal RAG evaluation belongs to Phase 9).*

---

## 4. Test Suite Execution & Verification

### 4.1 Pytest Execution Summary
- **Total Tests**: **158 passed** (0 failed, 0 errors)
- **Execution Time**: **10.97 seconds**
- **Test Breakdown**:
  - `tests/generation/test_context_builder.py`: 6 passed
  - `tests/generation/test_generators.py`: 9 passed
  - `tests/generation/test_prompts.py`: 3 passed
  - `tests/ingestion/test_chunking.py`: 15 passed
  - `tests/ingestion/test_cleaners.py`: 4 passed
  - `tests/ingestion/test_content_identity.py`: 3 passed
  - `tests/ingestion/test_loaders.py`: 7 passed
  - `tests/ingestion/test_metadata.py`: 2 passed
  - `tests/ingestion/test_provenance.py`: 3 passed
  - `tests/ingestion/test_structure_detector.py`: 9 passed
  - `tests/integration/test_baseline_rag_integration.py`: 6 passed
  - `tests/integration/test_hybrid_rag_integration.py`: 3 passed
  - `tests/integration/test_pipeline.py`: 2 passed
  - `tests/integration/test_vector_retrieval_integration.py`: 5 passed
  - `tests/retrieval/test_academic_tokenizer.py`: 8 passed
  - `tests/retrieval/test_benchmark.py`: 2 passed
  - `tests/retrieval/test_bm25.py`: 9 passed
  - `tests/retrieval/test_embeddings.py`: 21 passed
  - `tests/retrieval/test_fusion.py`: 7 passed
  - `tests/retrieval/test_hybrid_retriever.py`: 6 passed
  - `tests/retrieval/test_indexer.py`: 4 passed
  - `tests/retrieval/test_retriever.py`: 6 passed
  - `tests/retrieval/test_vectorstore.py`: 14 passed
  - `tests/test_foundation.py`: 4 passed

### 4.2 Linting & Formatting Check
- `python -m ruff check .`: **All checks passed!**

### 4.3 CLI Verifications

#### 1. Batch Indexing & Idempotency
```bash
python scripts/build_bm25_index.py --force-rebuild
# Total chunks submitted: 3 | New chunks indexed: 3 | Duration: 0.0031 s
python scripts/build_bm25_index.py
# Total chunks submitted: 3 | New chunks indexed: 0 | Chunks skipped: 3 (100% idempotent)
```

#### 2. Side-by-Side Diagnostic Search (`scripts/search_hybrid.py`)
```bash
python scripts/search_hybrid.py --query "23CSE302T"
# Top-1: doc_syllabus_23cse302t_chunk_0001
#   Fused Score: 0.016393 (Normalized: 1.0000)
#   Dense Rank : #1 (Score: 0.6209) | Lexical Rank: #1 (Score: 1.0000)
#   Dense Latency: 8.08 ms | Lexical Latency: 0.08 ms | Total: 8.24 ms
```

#### 3. End-to-End RAG Queries across Modes (`scripts/rag_query.py`)
- **Hybrid Mode**:
  ```bash
  python scripts/rag_query.py --query "What is taught in 23CSE302T?" --retrieval-mode hybrid
  # Answer: Grounded in 23CSE302T syllabus chunk. Total time: 4.01 ms.
  ```
- **Lexical Mode**:
  ```bash
  python scripts/rag_query.py --query "When are the mid examinations scheduled?" --retrieval-mode lexical
  # Answer: Mid-Semester Examination I & II dates returned. Total time: 3.58 ms.
  ```

---

## 5. Strict Boundaries & Compliance Checklist

- [x] **Zero RYU references**: Verified via automated codebase scans.
- [x] **Specification files untouched**: `framework.md` (23,551 B), `RAG.md` (34,509 B), `roadmap.md` (26,907 B), `agent.md` (46,214 B) are 100% byte-for-byte identical.
- [x] **No Phase Creep**:
  - NO Cross-encoder reranking (Phase 6).
  - NO Query expansion or HyDE (Phase 7).
  - NO Formal claim extraction or citation verification (Phase 8).
  - NO Full RAG benchmark evaluation suite (Phase 9).
  - NO Web UI / frontend (Phase 10).
- [x] **Mathematical correctness**: Robertson non-negative IDF, length normalization, zero-division guards.
- [x] **Content-hash freshness**: SHA-256 chunk delta tracking across UNCHANGED, MODIFIED, NEW, and REMOVED.
- [x] **Transparent calibration status**: RRF documented as rank-aggregation, not probability; weighted $\alpha=0.50$ documented as heuristic.

---

## 6. Readiness for Phase 6 (Retrieval Enhancement)

Phase 5 is complete. The system is fully ready for **Phase 6 — Retrieval Enhancement**:
- Decoupled `BaseRetriever` protocol allows Phase 6 to insert cross-encoder rerankers and top-K filters cleanly between `HybridRetriever` candidate pooling and `BaselineRAGPipeline`.
