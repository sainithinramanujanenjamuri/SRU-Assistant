# SRU Assistant — Technical Claims & Evidence Register

**Audit Target:** SRU Assistant: A RAG Framework for University Academic Query Resolution  
**Audit Standard:** Strict Source Verification & Traceability (Read-Only Codebase Inspection)  
**Verification Date:** November 2026  

---

## 1. Traceability & Evidence Status Categories

- **VERIFIED IMPLEMENTATION**: Verified directly through source code inspection, function invocation signatures, class declarations, and runtime data stores.
- **IMPLEMENTATION PRESENT — RUNTIME BEHAVIOR NOT VERIFIED**: Code is present in the repository, but execution requires specific hardware, external live services (e.g. GPU, live Ollama daemon), or specialized environments.
- **PROPOSED / NOT IMPLEMENTED**: Mentioned in early design proposals or comments, but no executable code exists in the repository.
- **NOT VERIFIED FROM SOURCE**: Claim cannot be corroborated by code, database records, or test suites.

---

## 2. Core Feature & Architecture Evidence Register

| Feature / Claim | Source File | Class / Method / Symbol | Verification Evidence & Line Reference | Verification Status |
| :--- | :--- | :--- | :--- | :---: |
| **FastAPI REST API Core** | `app/main.py` | `app = FastAPI(...)` | Lines 16-22: Configures `/docs`, `/redoc`, and CORS middleware | **VERIFIED IMPLEMENTATION** |
| **Static Frontend Mount** | `app/main.py` | `app.mount("/static", ...)` | Lines 37-47: Mounts `frontend/` directory to `/static` and serves `index.html` at `/` | **VERIFIED IMPLEMENTATION** |
| **End-to-End Query API** | `app/api/routes.py` | `answer_academic_query()` | Lines 20-39: `POST /api/query` receives `QueryRequest` and invokes `RAGQueryService.query()` | **VERIFIED IMPLEMENTATION** |
| **Document Upload Route** | `app/api/routes.py` | `upload_academic_document()` | Lines 42-128: `POST /api/documents/upload` enforces 64 KB streaming read up to 25 MB max limit | **VERIFIED IMPLEMENTATION** |
| **Document Catalog API** | `app/api/routes.py` | `list_academic_documents()` | Lines 130-135: `GET /api/documents` reads chunk metadata summaries from `documents/chunks/*.json` | **VERIFIED IMPLEMENTATION** |
| **System Health API** | `app/api/routes.py` | `healthcheck()` | Lines 137-142: `GET /api/health` queries vectorstore record count, BM25 status, and Ollama reachability | **VERIFIED IMPLEMENTATION** |
| **Prompt Injection Protection**| `app/security/query_guard.py` | `QueryGuard.inspect_query()` | Lines 40-95: Evaluates query length and screens against prompt injection patterns (`ignore previous instructions`, etc.) | **VERIFIED IMPLEMENTATION** |
| **Conversational Query Bypass**| `app/security/query_guard.py` | `QueryGuard.is_conversational` | Lines 96-120: Recognizes greetings and university identity questions without triggering vector retrieval | **VERIFIED IMPLEMENTATION** |
| **Document Security Guard** | `app/security/document_guard.py` | `DocumentGuard.validate_file_content()`| Lines 48-115: Validates file extensions (`.pdf`, `.docx`, `.txt`), magic bytes, and tracks duplicate SHA-256 hashes | **VERIFIED IMPLEMENTATION** |
| **Multi-Format Document Loaders**| `ingestion/loaders/` | `PDFLoader`, `DocxLoader`, `TextLoader`| `pdf_loader.py` L22 (`pypdf`), `docx_loader.py` L20 (`python-docx`), `txt_loader.py` L16 | **VERIFIED IMPLEMENTATION** |
| **Conservative Text Cleaner** | `ingestion/processors/cleaner.py`| `DocumentCleaner.clean()` | Lines 25-85: Removes running headers and footers exceeding 0.8 page frequency threshold | **VERIFIED IMPLEMENTATION** |
| **Structure-Aware Chunking** | `ingestion/chunking/structure_aware.py`| `StructureAwareChunker` | Lines 25-180: Chunks text prioritizing semantic headings, tables, and lists (Target: 500, Max: 1200 tokens) | **VERIFIED IMPLEMENTATION** |
| **SQLite Vector Store** | `retrieval/vectorstore/sqlite_store.py`| `SQLiteVectorStore` | Lines 35-190: Manages `index_manifest` and `vector_records` tables with binary vector storage and cosine distance | **VERIFIED IMPLEMENTATION** |
| **FastHash Embedding Model** | `retrieval/embeddings/fast_hash.py` | `FastHashEmbeddingModel` | Lines 22-80: 384-dimensional deterministic projection baseline for offline testing and fast CI | **VERIFIED IMPLEMENTATION** |
| **Ollama Neural Embeddings** | `retrieval/embeddings/ollama.py` | `OllamaEmbeddingModel` | Lines 25-95: Generates deep semantic vector embeddings via Ollama `/api/embeddings` | **IMPLEMENTATION PRESENT — RUNTIME BEHAVIOR NOT VERIFIED** |
| **Okapi BM25 Lexical Engine** | `retrieval/lexical/bm25.py` | `BM25Index`, `BM25Retriever` | Lines 35-210: Computes term frequency saturation and inverted document frequency ($k_1=1.5, b=0.75$) | **VERIFIED IMPLEMENTATION** |
| **Reciprocal Rank Fusion (RRF)**| `retrieval/fusion/rrf.py` | `ReciprocalRankFusion.fuse()`| Lines 9-115: Merges dense and lexical candidate rankings using formula $RRF(d) = \sum \frac{w_m}{k + rank_m(d)}$ ($k=60$) | **VERIFIED IMPLEMENTATION** |
| **Cross-Feature Re-ranking** | `retrieval/reranking/deterministic.py`| `DeterministicCrossFeatureReranker`| Lines 14-125: Re-ranks hybrid candidates using query token coverage and entity proximity | **VERIFIED IMPLEMENTATION** |
| **Neural Cross-Encoder Reranker**| `retrieval/reranking/transformer.py`| `TransformerReranker` | Lines 18-95: Uses `sentence_transformers.CrossEncoder` (`ms-marco-MiniLM-L-6-v2`) | **IMPLEMENTATION PRESENT — RUNTIME BEHAVIOR NOT VERIFIED** |
| **Academic Query Intent Analyzer**| `retrieval/query/analyzer.py` | `AcademicQueryAnalyzer.analyze_query()`| Lines 20-110: Extracts course codes, regulations, exam terms, and semesters from user queries | **VERIFIED IMPLEMENTATION** |
| **Candidate Metadata Filtering**| `retrieval/filtering/metadata_filter.py`| `MetadataFilter.filter_candidates()`| Lines 22-105: Adjusts candidate relevance scores based on query metadata alignment (soft boost: +0.15, penalty: -0.15) | **VERIFIED IMPLEMENTATION** |
| **Ollama LLM Integration** | `generation/llm/ollama.py` | `OllamaLLMClient.generate()` | Lines 134-262: Communicates with local Ollama daemon via `/api/chat`, strips `<think>` reasoning tags | **VERIFIED IMPLEMENTATION** |
| **Context Token Budgeting** | `generation/prompts/context_builder.py`| `ContextBuilder.build_context()`| Lines 25-95: Compiles retrieved chunks within a strict 1500-token budget, eliminating duplicates | **VERIFIED IMPLEMENTATION** |
| **Grounded System Prompting** | `generation/prompts/templates.py`| `GroundedPromptTemplate` | Lines 30-110: Formats system instructions enforcing strict evidence grounding and fallback tokens | **VERIFIED IMPLEMENTATION** |
| **Cross-Document Conflict Check**| `generation/grounding/conflict_detector.py`| `ConflictDetector.detect_conflicts()`| Lines 25-115: Flags conflicting dates and regulation rules across retrieved passages | **VERIFIED IMPLEMENTATION** |
| **Factual Claim Extraction** | `citations/claim_extractor.py`| `ClaimExtractor.extract_claims()`| Lines 25-90: Segments generated answers into atomic factual claims | **VERIFIED IMPLEMENTATION** |
| **Deterministic Citation Audit**| `citations/citation_verifier.py`| `CitationVerifier.verify_citations()`| Lines 41-155: Audits claims against cited chunk evidence; calculates Precision, Recall, and Support Score | **VERIFIED IMPLEMENTATION** |
| **Transactional Ingestion Rollback**| `app/services/query_service.py`| `RAGQueryService.ingest_and_index_file()`| Lines 388-474: Multi-stage try-except rolls back BM25, SQLite records, chunks JSON, and processed JSON on failure | **VERIFIED IMPLEMENTATION** |
| **Student-First Redesigned UI**| `frontend/index.html`, `app.js` | Single-Page Application (SPA) | Clean separation between Student Assistant and System Admin view; 4 starter cards; evidence modal | **VERIFIED IMPLEMENTATION** |
| **Optical Character Recognition**| `ingestion/loaders/pdf_loader.py`| — | Scanned image-based PDFs produce empty text; OCR engine (Tesseract/Surya) is NOT implemented | **PROPOSED / NOT IMPLEMENTED** |
| **Document Deletion API** | `app/api/routes.py` | — | No `DELETE /api/documents/{doc_id}` endpoint exists to purge documents from DB and index | **PROPOSED / NOT IMPLEMENTED** |
| **Role-Based Access Control** | `app/api/routes.py` | — | Upload endpoint has no authentication or role gating; open to any network client | **PROPOSED / NOT IMPLEMENTED** |

---

## 3. Benchmark Reproducibility & Empirical Verification

Empirical results verified directly from `data/benchmarks/rag_evaluation_report.json` (Dataset Version 1.0.0, 16 Queries across 10 Academic Categories):

| Metric | Experiment A: Vector RAG (Dense Only) | Experiment B: Hybrid RAG (Dense + BM25) | Experiment C: Hybrid + Re-ranking | Experiment D: Full Grounded Pipeline |
| :--- | :---: | :---: | :---: | :---: |
| **Recall@1** | 0.3438 | 0.5000 | 0.5625 | 0.5625 |
| **Recall@3** | 0.7188 | 0.7812 | 0.7812 | 0.7812 |
| **Recall@5** | 0.7188 | 0.8125 | 0.8125 | 0.8125 |
| **Precision@1** | 0.3750 | 0.5625 | 0.6250 | 0.6250 |
| **Precision@3** | 0.2708 | 0.3125 | 0.3333 | 0.3333 |
| **Precision@5** | 0.1625 | 0.1875 | 0.1875 | 0.1875 |
| **MRR (Mean Reciprocal Rank)** | 0.5625 | 0.6719 | 0.7083 | 0.7083 |
| **nDCG@5** | 0.5718 | 0.6859 | 0.7191 | 0.7191 |
| **Groundedness (Faithfulness)**| 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Unsupported Claim Rate** | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| **Citation Precision** | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| **Citation Recall** | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
