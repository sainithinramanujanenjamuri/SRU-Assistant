# Phase 3 — Embedding & Vector Store: Completion Report

**Project**: SRU Assistant: A RAG Framework for University Academic Query Resolution  
**Phase**: Phase 3 — Embedding & Vector Store  
**Status**: COMPLETE & VERIFIED  
**Date**: 2026-09-16  

---

## 1. Executive Summary

Phase 3 established the persistent vector knowledge base and semantic similarity retrieval layer for SRU Assistant. In strict accordance with the development roadmap (`roadmap.md`), RAG architecture specification (`RAG.md`), and the 23 Engineering Amendments, Phase 3 implements:
1. **Modular Embedding Subsystem**: Clean `BaseEmbeddingModel` abstraction with L2 unit normalization, dimension validation, batching, and three provider adapters:
   - `FastHashEmbeddingModel`: Deterministic lexical-feature embedding baseline for offline testing, CI, and zero-network local development.
   - `OllamaEmbeddingModel`: Local neural embedding adapter with health checks and informative missing-model errors.
   - `SentenceTransformersEmbeddingModel`: Optional adapter for Hugging Face sentence transformers.
2. **Index Identity & Manifest**: Strict vector index manifest (`IndexManifest`) recording provider, model, dimension, metric, and version. Query-time compatibility check (`IndexCompatibilityError`) prevents silent vector corruption.
3. **Persistent Local Vector Store (`SQLiteVectorStore`)**: SQLite database with WAL mode and binary float32 BLOB vector storage, supporting SQL metadata pre-filtering (`department`, `semester`, `regulation`, `academic_year`, `document_type`), vectorized NumPy dot-product cosine similarity, and deterministic tie-breaking.
4. **Idempotent Vector Indexer (`VectorIndexer`)**: Batched indexing pipeline tracking SHA-256 `chunk_content_hash` to safely skip unchanged chunks while updating modified content.
5. **Retrieval API & CLI Tools**: `VectorRetriever` exposing `search(query, top_k, filters)`, returning both raw cosine similarity in $[-1.0, 1.0]$ and min-max normalized score in $[0.0, 1.0]$ with preserved metadata and provenance, complemented by CLI utilities `scripts/build_vector_index.py` and `scripts/search_chunks.py`.

---

## 2. Architecture & Design Decisions

### 2.1 Embedding Models & FastHash Accurate Positioning
Per Amendment 1, `FastHashEmbeddingModel` is explicitly documented as a **deterministic lexical-feature embedding baseline**, NOT a neural semantic model. It projects word tokens and character 3/4-grams into a fixed 384-dimensional unit vector space using sign-hashing. It enables sub-millisecond, zero-dependency, 100% reproducible testing without network or daemon dependencies.

### 2.2 Neural Provider Availability Status
Per Amendment 2, neural providers were directly audited against the local environment:
- **Ollama**: Daemon active on `http://localhost:11434`, but dedicated embedding model `nomic-embed-text` is not pulled (the available models are generative LLMs: `qwen3.5:4b`, `gemma4:12b`, `qwen3.5:0.8b`, `qwen3.5:2b`, `qwen2.5-coder:3b`).
- **SentenceTransformers**: `sentence-transformers` package is not installed in the local environment.
- **Audit Conclusion**: *"Neural embedding evaluation unavailable in current environment."* All unit and integration tests successfully run on the deterministic FastHash baseline.

### 2.3 Exact Cosine Similarity & Score Definitions
Per Amendment 4, for unit-normalized vectors $\mathbf{q}$ and $\mathbf{d}$ ($||\mathbf{q}||_2 = 1.0, ||\mathbf{d}||_2 = 1.0$):
$$\text{cosine\_similarity} = \mathbf{q} \cdot \mathbf{d} \in [-1.0, 1.0]$$
$$\text{normalized\_score} = \frac{\text{cosine\_similarity} + 1.0}{2.0} \in [0.0, 1.0]$$
Both scores are stored and exposed on every `VectorSearchResult`.

### 2.4 Index Identity & Compatibility Enforcement
Per Amendment 3, every persisted vector store maintains an `index_manifest` record:
```json
{
  "embedding_provider": "fasthash",
  "embedding_model": "fasthash-384",
  "embedding_dimension": 384,
  "distance_metric": "cosine",
  "index_version": "1.0.0",
  "created_at": "2026-09-16T09:22:18.123456+00:00",
  "total_vectors": 3
}
```
Before querying, `VectorRetriever` verifies that the query model's provider, model name, and dimensionality match the stored manifest. Incompatibilities immediately raise `IndexCompatibilityError`, refusing queries and instructing that re-indexing is required.

### 2.5 SQLiteVectorStore Schema & Persistence
Per Amendment 5 and 6, `SQLiteVectorStore` is positioned as: *"Persistent local vector store suitable for the SRU Assistant prototype, evaluation, and local deployment."*

**Schema**:
```sql
CREATE TABLE IF NOT EXISTS index_manifest (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    embedding_provider TEXT NOT NULL,
    embedding_model TEXT NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    distance_metric TEXT NOT NULL,
    index_version TEXT NOT NULL,
    created_at TEXT NOT NULL,
    total_vectors INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS vector_records (
    chunk_id TEXT PRIMARY KEY,
    document_id TEXT NOT NULL,
    text TEXT NOT NULL,
    chunk_content_hash TEXT NOT NULL,
    vector BLOB NOT NULL,
    metadata_json TEXT NOT NULL,
    provenance_json TEXT NOT NULL,
    department TEXT,
    semester TEXT,
    regulation TEXT,
    academic_year TEXT,
    document_type TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_doc_id ON vector_records(document_id);
CREATE INDEX IF NOT EXISTS idx_dept ON vector_records(department);
CREATE INDEX IF NOT EXISTS idx_sem ON vector_records(semester);
CREATE INDEX IF NOT EXISTS idx_reg ON vector_records(regulation);
CREATE INDEX IF NOT EXISTS idx_year ON vector_records(academic_year);
CREATE INDEX IF NOT EXISTS idx_type ON vector_records(document_type);
```

### 2.6 Idempotency & Stale Detection
Per Amendments 7 and 8:
- Computes `chunk_content_hash = SHA256(chunk.text)`.
- If `chunk_id` already exists with identical hash $\rightarrow$ skipped without re-embedding.
- If `chunk_id` exists but hash differs $\rightarrow$ text modified, vector recomputed, record updated.
- If `chunk_id` is new $\rightarrow$ embedded in batch and inserted.

### 2.7 Search Determinism
Per Amendment 16, candidate chunks are ranked by:
1. `cosine_similarity` descending
2. `chunk_id` ascending (tie-breaker)

---

## 3. Empirical Benchmarks & Measured Metrics

Per Amendments 18 and 20, benchmarks were executed on the active system:

### 3.1 FastHash Latency & Throughput Benchmark (100 synthetic text samples)
- **Model**: `fasthash-384` (384 dimensions)
- **Single Latency**: 0.10 ms / chunk (throughput: ~10,477 chunks/sec)
- **Batch Latency**: 0.10 ms / chunk (throughput: ~10,078 chunks/sec)
- **Max L2 Normalization Error**: $4.86 \times 10^{-8}$ (virtually zero error)

### 3.2 Preliminary Academic Retrieval Benchmark (Synthetic SR University Evaluation Set)
- **Queries Evaluated**: 4
- **Corpus Size**: 4 representative institutional chunks (mid exams, syllabus trees, attendance regulation, academic calendar)
- **Mean Reciprocal Rank (MRR)**: **0.8750**
- **Recall@1**: **0.7500**
- **Recall@3**: **1.0000**
- **Recall@5**: **1.0000**

*(Note: Formal RAG retrieval benchmarking and comprehensive evaluation remain part of Phase 9).*

---

## 4. Test Suite Execution & Verification

### 4.1 Pytest Execution Summary
- **Total Tests**: **101 passed** (0 failed, 0 errors)
- **Execution Time**: **4.85 seconds**
- **Breakdown**:
  - `tests/ingestion/test_chunking.py`: 15 passed
  - `tests/ingestion/test_cleaners.py`: 4 passed
  - `tests/ingestion/test_content_identity.py`: 3 passed
  - `tests/ingestion/test_loaders.py`: 7 passed
  - `tests/ingestion/test_metadata.py`: 2 passed
  - `tests/ingestion/test_provenance.py`: 3 passed
  - `tests/ingestion/test_structure_detector.py`: 9 passed
  - `tests/integration/test_pipeline.py`: 2 passed
  - `tests/integration/test_vector_retrieval_integration.py`: 5 passed
  - `tests/retrieval/test_benchmark.py`: 2 passed
  - `tests/retrieval/test_embeddings.py`: 21 passed
  - `tests/retrieval/test_indexer.py`: 4 passed
  - `tests/retrieval/test_retriever.py`: 6 passed
  - `tests/retrieval/test_vectorstore.py`: 14 passed
  - `tests/test_foundation.py`: 4 passed

### 4.2 Linting & Formatting Check
- `python -m ruff check .`: **All checks passed!**

### 4.3 CLI Verification
1. **Empty Vector Store Search**:
   ```bash
   python scripts/search_chunks.py --query "When are the mid examinations scheduled?"
   # Safely returns: "No matching chunks found in the vector store."
   ```
2. **Batch Indexing (`scripts/build_vector_index.py`)**:
   - Initial run: Ingested 2 datasets (3 chunks) $\rightarrow$ 3 new vectors inserted in 0.01s.
   - Second run: Verified idempotency $\rightarrow$ 3 unchanged skipped in 0.00s.
3. **Interactive Search (`scripts/search_chunks.py`)**:
   - Query: *"When are the mid examinations scheduled?"*
     - Rank #1: `doc_calendar_2026_27_chunk_0000` (Cosine: `+0.2166`, Score: `0.6083`)
   - Query: *"tree traversals and graph algorithms"*
     - Rank #1: `doc_syllabus_23cse302t_chunk_0001` (Cosine: `+0.5050`, Score: `0.7525`)
   - Query with Filter: `department="Computer Science and Engineering"`
     - Pre-filtering successfully restricted candidates to CSE chunks only.

---

## 5. Strict Boundaries & Compliance Checklist

- [x] **Zero RYU references**: Verified via automated codebase scans.
- [x] **Specification files untouched**: `framework.md` (23,551 B), `RAG.md` (34,509 B), `roadmap.md` (26,907 B), `agent.md` (46,214 B) are 100% byte-for-byte intact.
- [x] **No Phase Creep**: No BM25, no hybrid fusion, no reranking, no LLM generation, no citations, no UI.
- [x] **Vector store persistence**: SQLite with WAL mode on disk verified across reload.
- [x] **Index manifest & validation**: Strict compatibility checks enforced.
- [x] **Full metadata/provenance preservation**: Downstream Phase 4 RAG consumption uninhibited.

---

## 6. Readiness for Phase 4 (Baseline RAG)

Phase 3 is complete. The system is fully ready for **Phase 4 — Baseline RAG**:
- Vector knowledge base is queryable via `VectorRetriever.search(query, top_k, filters)`.
- Retrieved `VectorSearchResult` objects contain the exact chunk text, document identifiers, section hierarchy, page numbers, and cosine similarity scores needed by Phase 4 context builders and LLM prompt templates.
