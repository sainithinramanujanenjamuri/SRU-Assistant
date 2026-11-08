# Repository Map: SRU Assistant

## 1. System Overview
**SRU Assistant** is an institutional Retrieval-Augmented Generation (RAG) framework developed for academic query resolution at SR University. It is engineered with strict grounding, hallucination mitigation, verified citations with page-level provenance, hybrid dense/lexical search, reciprocal rank fusion (RRF), re-ranking, and telemetry.

---

## 2. Directory Structure & Module Boundaries

```
SRU_Assistant_Capstone_Project/
├── app/                                 # Web Application & API Layer (FastAPI)
│   ├── api/
│   │   ├── routes.py                    # REST API routes: /query, /documents/upload, /documents, /health
│   │   └── schemas.py                   # Pydantic request/response models
│   ├── config/
│   │   └── settings.py                  # Pydantic BaseSettings loading from .env & environment
│   ├── security/
│   │   ├── document_guard.py            # File upload validation, size caps, magic bytes, hash dedup
│   │   ├── query_guard.py               # Prompt injection defense, query length, safe refusal
│   │   └── telemetry.py                 # Structured latency, token, and threat observability logging
│   ├── services/
│   │   └── query_service.py             # Singleton RAGQueryService orchestrating pipeline & indexing
│   └── main.py                          # FastAPI application entrypoint, CORS, static mounting
│
├── ingestion/                           # Document Intelligence & Knowledge Preparation (Phase 1 & 2)
│   ├── chunking/
│   │   ├── base.py                      # BaseChunker abstract interface
│   │   ├── fixed_window.py              # Fixed-size overlapping token chunker
│   │   ├── structure_aware.py           # Heading, table, and paragraph aware chunker
│   │   ├── tokenizer.py                 # Academic and generic whitespace/character tokenizer
│   │   └── pipeline.py                  # ChunkingPipeline generating chunk datasets
│   ├── loaders/
│   │   ├── base.py                      # BaseDocumentLoader abstract interface & loading exceptions
│   │   ├── docx_loader.py               # python-docx parser extracting paragraphs and tables
│   │   ├── factory.py                   # DocumentLoaderFactory mapping extensions (.pdf, .docx, .txt)
│   │   ├── pdf_loader.py                # pypdf parser extracting text and page numbers
│   │   └── txt_loader.py                # Plaintext reader with fallback encoding handling
│   ├── metadata/
│   │   └── extractor.py                 # Rule-based metadata extraction (title, academic year, category)
│   ├── processors/
│   │   ├── cleaner.py                   # Whitespace normalization, header/footer suppression
│   │   ├── structure_detector.py        # Table and heading hierarchy boundary detector
│   │   └── detectors/                   # Academic entity detectors (semester, regulation, course code)
│   ├── models.py                        # Document, RawDocument, ProcessedDocument data models
│   └── pipeline.py                      # DocumentPipeline orchestrating loader -> cleaner -> extractor
│
├── retrieval/                           # Dense, Lexical & Hybrid Retrieval (Phases 3, 5 & 6)
│   ├── bm25/
│   │   ├── academic_tokenizer.py        # Stopword filtering, stemming, punctuation handling
│   │   ├── indexer.py                   # Inverted index construction and persistence
│   │   ├── models.py                    # BM25Index, TermPostings, DocumentRecord models
│   │   └── retriever.py                 # Okapi BM25 scoring with k1 and b parameters
│   ├── embeddings/
│   │   ├── base.py                      # BaseEmbeddingModel interface
│   │   ├── factory.py                   # Embedding factory (fasthash, ollama, sentence_transformers)
│   │   ├── fasthash.py                  # Lightweight deterministic hashing baseline embedding (384-dim)
│   │   ├── ollama.py                    # Ollama REST embedding client
│   │   └── transformer.py               # HuggingFace sentence-transformers adapter
│   ├── fusion/
│   │   └── rrf.py                       # Reciprocal Rank Fusion algorithm with smoothing parameter k
│   ├── query/
│   │   ├── analyzer.py                  # Academic query intent classifier, course code & year extractor
│   │   └── metadata_filter.py           # Pre/post retrieval metadata filtering (exact, flexible, none)
│   ├── reranking/
│   │   ├── base.py                      # BaseReranker interface
│   │   ├── deterministic.py             # Lexical overlap and exact entity match reranker
│   │   ├── factory.py                   # Reranker factory (deterministic, passthrough, transformer, ollama)
│   │   ├── ollama.py                    # LLM-based reranking prompt adapter
│   │   ├── passthrough.py               # Identity no-op reranker
│   │   └── transformer.py               # Cross-encoder transformer reranker
│   ├── vectorstore/
│   │   ├── base.py                      # BaseVectorStore interface
│   │   ├── indexer.py                   # Vector database indexer
│   │   ├── retriever.py                 # Cosine similarity dense vector retriever
│   │   └── sqlite_store.py              # SQLite vector database with blob-encoded float32 embeddings
│   ├── base.py                          # BaseRetriever abstract class
│   ├── enhanced_retriever.py            # EnhancedRetriever combining Hybrid + Filter + Reranker
│   ├── hybrid_retriever.py              # HybridRetriever combining Dense + BM25 via RRF
│   └── models.py                        # RetrievalResult, RetrievedChunk, SearchQuery models
│
├── generation/                          # Generation, Grounding & Citations (Phases 4, 7 & 8)
│   ├── grounding/
│   │   ├── conflict_detector.py         # Multi-document contradiction detection (dates, credits, grades)
│   │   └── validator.py                 # N-gram overlap, claim entailment, unsupported claim detection
│   ├── llm/
│   │   ├── base.py                      # BaseGenerator interface
│   │   ├── deterministic.py             # Deterministic answer generator for unit testing & baselines
│   │   ├── factory.py                   # Generator factory (deterministic, ollama, openai_compatible)
│   │   ├── ollama.py                    # Ollama HTTP API client (/api/generate, /api/tags)
│   │   └── openai_compatible.py         # OpenAI-compatible /v1/chat/completions adapter
│   ├── prompts/
│   │   ├── context_builder.py           # Token-bounded context window formatter with citation tags
│   │   └── templates.py                 # Grounded institutional system prompts & fallback messages
│   ├── models.py                        # GenerationResponse, GroundingReport, ConflictReport models
│   └── pipeline.py                      # BaselineRAGPipeline orchestrating retrieval -> generation -> check
│
├── citations/                           # Citation Verification & Provenance (Phase 8)
│   ├── citation_mapper.py               # Inline bracket citation extractor and chunk identifier mapper
│   ├── citation_verifier.py             # Verifies claim textual support against source chunk text
│   ├── claim_extractor.py               # Sentence-level factual assertion extractor
│   ├── formatter.py                     # Citation style formatter (inline brackets, footnotes)
│   └── models.py                        # Citation, CitationVerificationReport, Claim models
│
├── evaluation/                          # RAG Benchmark & Metrics Suite (Phase 9)
│   ├── benchmark_loader.py              # Evaluates test datasets (JSON test fixtures)
│   ├── evaluator.py                     # RAGEvaluator executing benchmarks and reporting metrics
│   ├── generation_metrics.py            # Faithfulness, answer relevance, citation precision/recall
│   ├── models.py                        # EvaluationQuery, BenchmarkResult, MetricSummary models
│   └── retrieval_metrics.py             # Precision@k, Recall@k, MRR, nDCG@k
│
├── frontend/                            # University Web Portal Interface (Phase 10 & 14)
│   ├── index.html                       # Academic query portal UI (student/faculty mode)
│   ├── presentation.html                # Capstone viva presentation interactive slides
│   ├── app.js                           # Frontend client logic, API calls, citations rendering, tabs
│   └── styles.css                       # University-branded CSS (SR University styling, responsive layout)
│
├── data/                                # Persistent Databases and Evaluation Fixtures
│   ├── benchmarks/                      # Benchmark datasets (retrieval, grounding, citations, eval suite)
│   ├── indices/                         # Persistent BM25 inverted index JSON file
│   └── vectorstore/                     # Persistent SQLite vector database (sru_vectors.db)
│
├── documents/                           # Institutional Document Storage
│   ├── raw/                             # Official source documents (.pdf, .docx, .txt)
│   ├── processed/                       # Cleaned intermediate JSON documents
│   └── chunks/                          # Structured token chunk datasets with provenance
│
├── scripts/                             # Operational & Benchmarking CLI Utilities
│   ├── build_bm25_index.py              # Builds persistent BM25 index from chunk JSONs
│   ├── build_vector_index.py            # Embeds and indexes chunks into SQLite vector store
│   ├── prepare_chunks.py                # Runs chunking pipeline on processed documents
│   ├── rag_query.py                     # CLI query tool for interactive terminal queries
│   ├── search_chunks.py                 # Vector similarity search CLI
│   ├── search_hybrid.py                 # Hybrid RRF search CLI
│   ├── validate_documents.py            # Validates raw document directory
│   ├── evaluate_rag.py                  # End-to-end evaluation suite runner
│   ├── evaluate_citations.py            # Citation accuracy evaluation script
│   ├── evaluate_grounding.py            # Grounding and hallucination evaluation script
│   └── evaluate_retrieval_enhancement.py # Evaluates retrieval enhancement pipeline
│
└── tests/                               # Comprehensive Automated Test Suite (324 tests)
    ├── citations/                       # 30 tests for citation extraction, mapping, verification
    ├── evaluation/                      # 23 tests for benchmark loaders and metric formulas
    ├── generation/                      # 49 tests for generators, conflict detector, prompts, grounding
    ├── ingestion/                       # 43 tests for loaders, cleaners, chunking, structure detector
    ├── integration/                     # 28 tests for end-to-end pipeline, hybrid, citations, vectors
    ├── retrieval/                       # 126 tests for vectorstore, BM25, embeddings, RRF, reranking
    ├── test_api.py                      # 5 tests for FastAPI routes, health, documents, query
    ├── test_foundation.py               # 4 tests for settings, logging, environment
    └── test_reliability_security.py     # 20 tests for guards, rate limits, file validation, errors
```

