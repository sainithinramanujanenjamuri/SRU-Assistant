# SRU Assistant — Complete Repository Map & Module Inventory

**Project Title:** SRU Assistant — A Grounded Retrieval-Augmented Generation (RAG) Framework for University Academic Query Resolution  
**Institutional Context:** School of Computer Science & AI, SR University  
**Audit & Extraction Date:** November 2026  
**Auditor / Architect:** Principal Software Architect & QA Lead  

---

## 1. System Inventory Summary

- **Total Python Source Files:** 185
- **Core Architecture Layers:** 8 (Frontend, API/Security, Ingestion, Retrieval, Generation, Citations, Evaluation, Storage)
- **Active Embedding Model:** `fasthash-384` (384-dimensional lexical-semantic baseline)
- **Active LLM Provider:** `ollama` with `qwen3.5:4b` (`chat` endpoint mode, `<think>` strip handler)
- **Dual-Index Status:** 43 vector chunks in SQLite (`data/vectorstore/sru_vectors.db`), 43 chunks in BM25 (`data/indices/bm25_index.json`)

---

## 2. Comprehensive Module Inventory

### 2.1 API & Application Layer (`app/`)

| Module / File Path | Responsibility | Key Classes & Functions | Imports / Dependencies | Execution Role | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `app/main.py` | FastAPI application factory, middleware, static mounts | `app`, `serve_index()`, `serve_presentation()` | `fastapi`, `uvicorn`, `app.api.routes`, `app.config.settings` | Entry point for HTTP server and static file serving | Line 16: `app = FastAPI(...)`, Line 40: mounts `/static` |
| `app/api/routes.py` | HTTP endpoint controllers for queries, uploads, documents, health | `answer_academic_query()`, `upload_academic_document()`, `list_academic_documents()`, `healthcheck()` | `app.api.schemas`, `app.services.query_service`, `app.security` | Direct routing from client requests to RAG services | Line 20: `@router.post("/query")`, Line 42: `@router.post("/documents/upload")` |
| `app/api/schemas.py` | Pydantic v2 schemas defining API request and response contracts | `QueryRequest`, `QueryResponse`, `CitationDetail`, `VerificationSummary`, `DocumentSummary`, `DocumentUploadResponse`, `HealthResponse` | `pydantic` | Contract validation and serialization | Lines 10-97: Schema definitions |
| `app/config/settings.py` | Environment variable parsing, default parameters, validation | `Settings`, `get_settings()` | `pydantic_settings`, `functools.lru_cache` | Centralized system parameter source | Line 11: `class Settings(BaseSettings)` |
| `app/security/query_guard.py` | Query safety, prompt injection detection, conversational routing | `QueryGuard`, `QueryGuardResult`, `QuerySecurityError` | `re`, `logging` | Pre-retrieval query screening and sanitization | Line 40: `inspect_query(query)` |
| `app/security/document_guard.py` | Upload safety, file extension, magic-byte inspection, duplicate hash tracking | `DocumentGuard`, `DocumentValidationResult`, `DocumentSecurityError` | `hashlib`, `pathlib` | Pre-ingestion validation of uploaded files | Line 48: `validate_file_content(filename, content)` |
| `app/security/telemetry.py` | Request tracking, latency profiling, audit logging | `ObservabilityLogger`, `RequestTelemetry`, `generate_request_id()` | `json`, `time`, `uuid` | Structured logging and telemetry auditing | Line 35: `record_query(telemetry)` |
| `app/services/query_service.py` | Singleton service orchestrating RAG queries and ingestion lifecycle | `RAGQueryService`, `IngestionStageError` | `app.api.schemas`, `retrieval.*`, `generation.*`, `citations.*` | Central pipeline coordination engine | Line 55: `class RAGQueryService`, Line 162: `query()`, Line 376: `ingest_and_index_file()` |

---

### 2.2 Document Ingestion & Chunking (`ingestion/`)

| Module / File Path | Responsibility | Key Classes & Functions | Imports / Dependencies | Execution Role | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ingestion/pipeline.py` | End-to-end ingestion pipeline: load, clean, structure, metadata | `DocumentPipeline`, `IngestionBatchResult` | `ingestion.loaders`, `ingestion.processors`, `ingestion.metadata` | Converts raw `.pdf`, `.docx`, `.txt` to intermediate `ProcessedDocument` | Line 44: `class DocumentPipeline`, Line 60: `process_file()` |
| `ingestion/loaders/factory.py` | Factory pattern for loader dispatch based on extension | `DocumentLoaderFactory` | `pdf_loader`, `docx_loader`, `txt_loader` | Resolves appropriate loader | Line 15: `get_loader(file_path)` |
| `ingestion/loaders/pdf_loader.py` | PDF parsing and page-by-page text extraction | `PDFLoader` | `pypdf.PdfReader` | Extracts text and structural pages from PDF files | Line 22: `class PDFLoader(BaseDocumentLoader)` |
| `ingestion/loaders/docx_loader.py` | DOCX document and table cell extraction | `DocxLoader` | `docx.Document` | Parses Word documents, preserving paragraphs and tables | Line 20: `class DocxLoader(BaseDocumentLoader)` |
| `ingestion/loaders/txt_loader.py` | Plain text loading with encoding fallbacks | `TextLoader` | `pathlib` | Loads raw `.txt` files with UTF-8 / Latin-1 fallbacks | Line 16: `class TextLoader(BaseDocumentLoader)` |
| `ingestion/processors/cleaner.py` | Conservative text normalization, header/footer removal | `DocumentCleaner` | `re` | Strips repeating headers/footers exceeding threshold | Line 25: `clean(extracted_doc)` |
| `ingestion/processors/structure_detector.py` | Detects academic entities across text | `StructureDetector` | `detectors.*` | Aggregates dates, course codes, regulations, semesters | Line 24: `detect_structures(elements, text)` |
| `ingestion/metadata/extractor.py` | Computes document-level metadata and categorization | `MetadataExtractor` | `ingestion.models.DocumentMetadata` | Classifies document category, academic year, department | Line 25: `extract_metadata(extracted_doc, structures)` |
| `ingestion/chunking/structure_aware.py` | Hierarchy-aware chunking preserving tables and sections | `StructureAwareChunker` | `ingestion.chunking.tokenizer` | Splits document along semantic boundaries (Target: 500, Max: 1200) | Line 25: `class StructureAwareChunker(BaseChunker)` |
| `ingestion/chunking/tokenizer.py` | Token estimation and counting abstraction | `AcademicTokenizer`, `get_default_tokenizer()` | `re` | Calculates token budgets without heavy dependencies | Line 20: `count_tokens(text)` |

---

### 2.3 Retrieval Subsystem (`retrieval/`)

| Module / File Path | Responsibility | Key Classes & Functions | Imports / Dependencies | Execution Role | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `retrieval/vectorstore/sqlite_store.py` | Embedded vector database backed by SQLite | `SQLiteVectorStore`, `IndexManifest` | `sqlite3`, `struct` | Stores 384-d float vectors as binary BLOBs and computes cosine similarity | Line 35: `class SQLiteVectorStore`, Line 150: `similarity_search()` |
| `retrieval/vectorstore/retriever.py` | Dense vector channel retriever | `VectorRetriever` | `retrieval.embeddings` | Encodes query and retrieves top-k nearest vector records | Line 20: `retrieve(query, top_k)` |
| `retrieval/embeddings/fast_hash.py` | Deterministic lexical-semantic hashing embedder | `FastHashEmbeddingModel` | `hashlib`, `math` | 384-dimensional offline projection baseline | Line 22: `embed_query(text)`, `embed_documents(texts)` |
| `retrieval/embeddings/ollama.py` | Remote neural embeddings via Ollama `/api/embeddings` | `OllamaEmbeddingModel` | `httpx` | Generates deep semantic vector representations | Line 25: `class OllamaEmbeddingModel` |
| `retrieval/lexical/bm25.py` | BM25 lexical ranking engine with Okapi formula | `BM25Index`, `BM25Retriever` | `retrieval.lexical.tokenizer` | Lexical scoring with term frequency saturation (k1=1.5, b=0.75) | Line 35: `class BM25Index`, Line 140: `score(query_tokens)` |
| `retrieval/lexical/indexer.py` | Indexing manager for BM25 with incremental updates | `BM25Indexer` | `retrieval.lexical.bm25` | Builds and synchronizes `bm25_index.json` | Line 25: `index_chunks(chunks, prune_missing)` |
| `retrieval/fusion/rrf.py` | Reciprocal Rank Fusion of multi-modal ranked lists | `ReciprocalRankFusion` | `retrieval.models` | Combines dense and lexical candidates: $RRF(d) = \sum \frac{w_m}{k + rank_m(d)}$ | Line 9: `class ReciprocalRankFusion`, Line 44: `fuse()` |
| `retrieval/fusion/hybrid.py` | Orchestrates dual-channel retrieval and RRF fusion | `HybridRetriever` | `dense_retriever`, `bm25_retriever`, `rrf` | Executes parallel search across vector store and BM25 index | Line 25: `class HybridRetriever` |
| `retrieval/reranking/deterministic.py` | Rule-based cross-feature re-ranking baseline | `DeterministicCrossFeatureReranker` | `retrieval.lexical.tokenizer` | Reranks candidates based on query token coverage and entity proximity | Line 14: `class DeterministicCrossFeatureReranker` |
| `retrieval/reranking/transformer.py` | Neural cross-encoder reranker | `TransformerReranker` | `sentence_transformers.CrossEncoder` | Deep cross-attention score evaluation | Line 18: `class TransformerReranker` |
| `retrieval/query/analyzer.py` | Academic intent and entity extraction | `AcademicQueryAnalyzer` | `re` | Extracts course codes, regulations, exam types from user queries | Line 20: `analyze_query(query)` |
| `retrieval/filtering/metadata_filter.py` | Soft and hard candidate constraint filtering | `MetadataFilter` | `retrieval.models` | Adjusts candidate scores based on department/semester alignment | Line 22: `filter_candidates(candidates, constraints)` |
| `retrieval/enhanced_retriever.py` | Unified retrieval pipeline (Hybrid + Filter + Rerank) | `EnhancedRetriever` | `hybrid_retriever`, `reranker`, `query_analyzer` | Production retrieval pipeline used in Enhanced RAG mode | Line 28: `class EnhancedRetriever` |

---

### 2.4 Generation & Grounding Subsystem (`generation/`)

| Module / File Path | Responsibility | Key Classes & Functions | Imports / Dependencies | Execution Role | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `generation/pipeline.py` | End-to-end RAG synthesis pipeline | `BaselineRAGPipeline` | `retriever`, `generator`, `context_builder`, `grounding_validator` | Retrieves evidence, builds context, generates text, verifies grounding | Line 35: `class BaselineRAGPipeline`, Line 90: `answer_query()` |
| `generation/prompts/context_builder.py` | Context token budget enforcement and deduplication | `ContextBuilder` | `ingestion.chunking.tokenizer` | Assembles retrieved chunks into context within token budget (1500) | Line 25: `build_context(retrieved_chunks)` |
| `generation/prompts/templates.py` | Academic system prompts and instructions | `GroundedPromptTemplate` | — | Defines strict grounding instructions and fallback tokens | Line 30: `format_prompt(query, context)` |
| `generation/llm/ollama.py` | Ollama client adapter with thinking-tag stripping | `OllamaLLMClient` | `httpx`, `re` | Executes local LLM inference (`qwen3.5:4b`) via HTTP API | Line 14: `class OllamaLLMClient`, Line 134: `generate()` |
| `generation/llm/deterministic.py` | Rule-based generator for offline CI testing | `DeterministicGenerator` | — | Generates synthesized answers from retrieved passages deterministically | Line 20: `class DeterministicGenerator` |
| `generation/grounding/conflict_detector.py` | Detects cross-document factual discrepancies | `ConflictDetector` | `generation.grounding.entities` | Flags conflicting examination dates or regulation thresholds | Line 25: `detect_conflicts(evidence_items)` |
| `generation/grounding/validator.py` | Post-generation factual support validation | `GroundingValidator` | `re` | Validates whether generated claims align with evidence | Line 30: `validate_grounding(answer, evidence)` |

---

### 2.5 Citation Subsystem (`citations/`)

| Module / File Path | Responsibility | Key Classes & Functions | Imports / Dependencies | Execution Role | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `citations/claim_extractor.py` | Sentence splitting and factual claim extraction | `ClaimExtractor` | `re` | Breaks answer into verifiable atomic claims | Line 25: `extract_claims(answer)` |
| `citations/citation_mapper.py` | Maps claims to specific candidate source chunks | `CitationMapper` | `citations.models` | Maps citation IDs (`[1]`, `[2]`) to chunk IDs | Line 20: `map_citations_to_claims(claims, chunks)` |
| `citations/citation_verifier.py` | Deterministic claim-evidence factual audit | `CitationVerifier` | `generation.grounding.entities` | Calculates Citation Precision, Recall, and Overall Support Score | Line 12: `class CitationVerifier`, Line 41: `verify_citations()` |
| `citations/formatter.py` | Formats inline brackets and source blocks | `CitationFormatter` | `citations.models` | Injects bracket citations (`[1]`) into answer text | Line 22: `format_cited_answer(answer, citations)` |
| `citations/models.py` | Data structures for claims, citations, verifications | `CitationItem`, `ClaimItem`, `CitationVerificationResult` | `pydantic` | Standardizes citation data interchange | Lines 10-90: Model declarations |

---

### 2.6 Evaluation Subsystem (`evaluation/`)

| Module / File Path | Responsibility | Key Classes & Functions | Imports / Dependencies | Execution Role | Verification Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `evaluation/evaluator.py` | Orchestrates comprehensive benchmark execution | `RAGEvaluator` | `evaluation.retrieval`, `evaluation.generation` | Runs benchmark suite across Retrieval, Generation, and Citations | Line 30: `class RAGEvaluator` |
| `evaluation/retrieval/metrics.py` | Information Retrieval metrics | `compute_recall_at_k`, `compute_precision_at_k`, `compute_mrr`, `compute_ndcg_at_k` | `math` | Evaluates retrieval ranking quality against gold standard | Lines 10-120: Metric equations |
| `evaluation/generation/metrics.py` | RAG Triad generation metrics | `compute_groundedness`, `compute_answer_relevance`, `compute_context_relevance` | `re` | Evaluates faithfulness, relevance, and factual correctness | Lines 25-180: Metric equations |
| `evaluation/datasets/benchmark_loader.py` | Loads JSON evaluation datasets | `BenchmarkLoader` | `json`, `pathlib` | Ingests 16-query academic benchmark suite | Line 15: `load_benchmark(path)` |
| `evaluation/reports/report_generator.py` | Generates summary reports and markdown tables | `ReportGenerator` | `json` | Compiles comparative experiment evaluation tables | Line 20: `generate_markdown_report(report)` |
