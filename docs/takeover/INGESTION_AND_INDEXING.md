# Document Ingestion and Indexing Audit & Verification

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  
**Module:** Ingestion Pipeline, Chunking, Vector Storage, and BM25 Indexing  

---

## 1. Pipeline Architecture Overview

The SRU Assistant ingestion architecture transforms unstructured academic documents into structured, retrieval-ready chunks through a multi-stage deterministic pipeline:

```
[Raw Document (.pdf, .docx, .txt)]
               │
               ▼
   [DocumentLoaderFactory]  ────────► Checks magic bytes, extracts text & pages
               │
               ▼
      [DocumentCleaner]     ────────► Normalizes whitespace, strips running headers/footers
               │
               ▼
     [StructureDetector]    ────────► Detects headings, tables, regulations, course codes
               │
               ▼
     [ProcessedDocument]    ────────► JSON intermediate representation in documents/processed/
               │
               ▼
  [StructureAwareChunker]   ────────► Generates bounded chunks (target 500, overlap 100 tokens)
               │
               ▼
      [ChunkDataset]        ────────► JSON dataset container in documents/chunks/
         │          │
         ▼          ▼
  [VectorIndexer] [BM25Indexer] ───► Dual-channel indexing: SQLite vectorstore & BM25 inverted index
```

---

## 2. Ingestion Format Verification

| Document Format | Parser Implementation | Provenance Preserved | Status | Evidence |
| :--- | :--- | :--- | :--- | :--- |
| **PDF (.pdf)** | `pypdf` (`PDFLoader`) | 1-indexed page numbers, element IDs | **Verified** | `tests/ingestion/test_loaders.py::TestPDFLoader` |
| **DOCX (.docx)** | `python-docx` (`DOCXLoader`) | Paragraph & table element order, cell content | **Verified** | `tests/ingestion/test_loaders.py::TestDocxLoader` |
| **Plain Text (.txt)** | `TXTLoader` with encoding fallbacks (`utf-8`, `utf-8-sig`, `latin-1`) | 1-indexed line numbers | **Verified** | `tests/ingestion/test_loaders.py::TestTxtLoader` |

### Edge Case Handling
- **Empty / Stub Documents:** `EmptyDocumentError` raised if file is 0 bytes or below min threshold (10 bytes).
- **Corrupted Headers:** Magic bytes validation rejects corrupted PDF headers (`CorruptedDocumentError`).
- **Disallowed File Types:** Rejects executable binaries, scripts (`.sh`, `.exe`, `.bat`) with `DocumentSecurityError`.
- **Duplicate Document Detection:** Computes SHA-256 hash before saving; duplicate uploads return status `"duplicate"` without redundant reprocessing.

---

## 3. Chunking & Provenance Integrity

### Structure-Aware Chunking Strategy
- **Token Bounds:** Configured via `Settings` (`chunk_target_tokens=500`, `chunk_overlap_tokens=100`, `chunk_min_tokens=50`, `chunk_max_tokens=1200`).
- **Heading Continuity:** Chunks inherit hierarchical ancestral breadcrumbs (e.g., `Syllabus > Unit II > Trees`).
- **Table Preservation:** Tables are preserved as discrete Markdown chunks without destructive truncation across cells.
- **Deterministic Chunk IDs:** Follow format `{document_id}_chunk_{index:04d}`.
- **Traceability:** Every chunk maintains `ChunkProvenance` containing `document_id`, `source_file`, `page_numbers`, `line_numbers`, and contributing `element_ids`.

---

## 4. Indexing Systems & Synchronization

### 4.1 Dense Vector Store (`retrieval/vectorstore/sqlite_store.py`)
- **Backend:** SQLite at `data/vectorstore/sru_vectors.db`.
- **Vector Encoding:** Pure float32 binary blobs stored in `vector_records` table.
- **Metadata Indexing:** SQL B-tree indexes on `document_id`, `department`, `semester`, `regulation`, `academic_year`, and `document_type`.
- **Embedding Provider:** `fasthash` produces deterministic 384-dimensional unit-normalized embeddings locally on CPU without external API keys or GPU memory.
- **Idempotence:** `VectorIndexer` checks SHA-256 `chunk_content_hash`; identical chunks are skipped, updated chunks are replaced, and new chunks are inserted.

### 4.2 BM25 Inverted Index (`retrieval/lexical/bm25.py`)
- **Persistence:** JSON file at `data/indices/bm25_index.json`.
- **Tokenizer:** `AcademicTokenizer` handles compound university course codes (`23CSE302T`), semester markers (`Sem-VII`), and regulations (`R23`).
- **Scoring:** Okapi BM25 with configurable parameters $k_1 = 1.5$, $b = 0.75$.
- **Delta Tracking:** `BM25Indexer` supports incremental additions and state synchronization.

---

## 5. End-to-End Upload & Indexing Orchestration

### Integration Implementation
Previously, file upload validated and stored documents into `documents/raw/` but left chunking and indexing to manual CLI scripts. 

During takeover Phase 3:
1. Implemented `RAGQueryService.ingest_and_index_file(file_path: Path)` which:
   - Processes raw file via `DocumentPipeline`.
   - Chunks processed document via `ChunkingPipeline`.
   - Embeds and indexes chunks into `SQLiteVectorStore` via `VectorIndexer`.
   - Indexes terms into `BM25Index` and persists to disk via `BM25Indexer`.
2. Enhanced `POST /api/documents/upload` with optional `auto_index=True` query parameter.
3. Added automated test `tests/integration/test_upload_and_indexing_lifecycle.py` verifying that uploading a document with `auto_index=True` makes its facts immediately retrievable and citable via `/api/query`.

---

## 6. Protection of Existing Datasets
Before testing indexing modifications, complete backups of existing databases were generated in `data/backups/`:
- `data/backups/sru_vectors.db.bak`
- `data/backups/bm25_index.json.bak`

Original institutional datasets (Academic Calendar 2026-27, Academic Regulations R23, B.Tech CSE Syllabus Sem VII, and Capstone Approval Form) were preserved without data loss.

