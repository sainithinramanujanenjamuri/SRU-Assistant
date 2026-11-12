"""Structured content data for Chapters 1 through 6 of SRU Assistant technical documentation."""

CHAPTERS_PART1 = [
    {
        "id": "cover",
        "title": "SRU Assistant: A Grounded Retrieval-Augmented Generation (RAG) Framework for University Academic Query Resolution",
        "blocks": [
            ("cover_meta", {
                "title": "SRU ASSISTANT",
                "subtitle": "A Grounded Retrieval-Augmented Generation (RAG) Framework for University Academic Query Resolution",
                "doc_type": "Comprehensive Technical Architecture, System Extraction, Implementation Audit & Defense Guide",
                "author": "Capstone Engineering Team 235 & Principal AI Systems Architect",
                "department": "School of Computer Science & Artificial Intelligence",
                "institution": "SR UNIVERSITY, WARANGAL, TELANGANA",
                "date": "November 2026",
                "version": "1.0.0 (Production Release)",
                "classification": "Academic Capstone Technical Documentation"
            }),
            ("page_break",)
        ]
    },
    {
        "id": "ch1",
        "title": "1. Executive Summary & Project Objectives",
        "blocks": [
            ("heading_2", "1.1 Mission & Academic Institutional Context"),
            ("p", "SRU Assistant is an institutional Retrieval-Augmented Generation (RAG) system engineered to solve academic query resolution challenges across university ecosystems. In modern higher education institutions, essential academic knowledge—spanning undergraduate course regulations, credit distributions, examination timetables, prerequisite trees, and departmental circulars—is conventionally distributed across disparate, unstructured PDF files, Word circulars, and departmental web portals. Consequently, students, faculty mentors, and academic administrators expend hundreds of hours each semester manually cross-referencing conflicting documents to resolve routine inquiries regarding attendance condonation, grade point averages, and examination dates.", "Institutional Problem: "),
            ("p", "Standard commercial Large Language Models (LLMs) cannot reliably address university-specific queries. When queried about university-specific regulations, ungrounded commercial models hallucinate plausible-sounding but completely fabricated guidelines, invent nonexistent course codes, or confuse regulations across disparate academic years (e.g., conflating R20 and R23 regulation frameworks). SRU Assistant solves this vulnerability through a deterministic, evidence-first engineering philosophy: 'Retrieve first. Generate second. Cite every claim.' The system strictly anchors answer generation in verified university documents, executing claim-by-claim verification and providing interactive provenance chips that map back to official pages and sections.", "The Hallucination Dilemma: "),
            ("callout", "SRU Assistant strictly prohibits ungrounded parametric generation. If official institutional evidence is missing or insufficient, the system enforces a standardized fallback response ('INSUFFICIENT_EVIDENCE') rather than attempting creative interpolation. Factual claims must be supported by verifiable textual passages.", "CORE ARCHITECTURAL TENET"),
            ("heading_2", "1.2 Scope & Target Stakeholders"),
            ("p", "The primary target user is the undergraduate student navigating semester-wise academic requirements. Students interact with a calm, accessible Single-Page Application (SPA) designed to answer questions about examination dates, attendance rules, syllabi, and academic policies without exposing internal retrieval complexities. The secondary stakeholder is the university academic administrator, who utilizes a dedicated System & Administration panel to monitor real-time vector database synchronization, configure retrieval pipeline parameters (Enhanced, Hybrid, or Dense modes), and securely ingest newly approved circulars and curriculum plans.", "Stakeholder Matrix: "),
            ("heading_2", "1.3 Functional & Non-Functional Requirements Matrix"),
            ("p", "The system's implementation directly addresses the following verified functional and non-functional requirements:", "Requirements Verification: "),
            ("table", ["Requirement ID", "Category", "Specification Description", "Implementation Status", "Verification Method"], [
                ["FR-01", "Document Ingestion", "Parse official PDF, DOCX, and TXT documents preserving structural hierarchy and tables.", "VERIFIED IMPLEMENTATION", "ingestion/pipeline.py, tests/ingestion/"],
                ["FR-02", "Dual-Store Indexing", "Atomically index chunks into SQLite vector store (384-d) and BM25 inverted index.", "VERIFIED IMPLEMENTATION", "retrieval/vectorstore/, retrieval/lexical/"],
                ["FR-03", "Hybrid Rank Fusion", "Combine dense semantic search and BM25 lexical ranking via Reciprocal Rank Fusion (k=60).", "VERIFIED IMPLEMENTATION", "retrieval/fusion/rrf.py, tests/retrieval/"],
                ["FR-04", "Security Guard", "Detect prompt injection, enforce length bounds, and validate file magic-bytes/hashes.", "VERIFIED IMPLEMENTATION", "app/security/query_guard.py, document_guard.py"],
                ["FR-05", "Grounded Generation", "Generate natural language answers via local Ollama LLM (Qwen3.5:4b) at temperature 0.0.", "VERIFIED IMPLEMENTATION", "generation/llm/ollama.py, generation/pipeline.py"],
                ["FR-06", "Citation Audit", "Segment answers into claims and deterministically verify containment in cited chunks.", "VERIFIED IMPLEMENTATION", "citations/citation_verifier.py, claim_extractor.py"],
                ["NFR-01", "Data Privacy", "100% on-premises execution without cloud data egress or third-party API exposure.", "VERIFIED IMPLEMENTATION", "Local Ollama daemon & embedded SQLite"],
                ["NFR-02", "Query Latency", "End-to-end grounded query resolution under 2,500 ms (Retrieval < 25 ms, LLM < 2,000 ms).", "VERIFIED IMPLEMENTATION", "app/security/telemetry.py empirical logs"],
                ["NFR-03", "Zero Hallucination", "Achieve 0.0% unsupported claim rate on verified benchmark evaluation suites.", "VERIFIED IMPLEMENTATION", "data/benchmarks/rag_evaluation_report.json"]
            ]),
            ("page_break",)
        ]
    },
    {
        "id": "ch2",
        "title": "2. Complete System Architecture & Technology Stack",
        "blocks": [
            ("heading_2", "2.1 Multi-Tier Architecture Overview"),
            ("p", "SRU Assistant is organized as a decoupled, multi-tier system engineered around clean separation of concerns. The architecture consists of eight distinct logical layers: (1) Presentation Layer, (2) API & Security Gateway, (3) Service Orchestration Layer, (4) Ingestion & Preprocessing Subsystem, (5) Dual-Channel Retrieval Subsystem, (6) Local Neural Generation Subsystem, (7) Grounding & Citation Auditor, and (8) Persistent Storage Layer.", "Architectural Tiering: "),
            ("diagram", "diagram_01.png", "Figure 1: Overall System Architecture — Decoupled eight-tier RAG processing pipeline."),
            ("heading_2", "2.2 Layer Decomposition & Architectural Responsibilities"),
            ("p", "Each layer maintains strict encapsulation and communicates through immutable Pydantic contracts and abstract interfaces:", "Layer Boundaries: "),
            ("p", "The client-side single-page application is implemented using semantic HTML5, modern CSS3 variables, and vanilla ES6+ JavaScript. It provides a dual-view interface: a clean student conversational stream with citation chips and an administrative dashboard for pipeline inspection. It requires zero Node.js build dependencies, ensuring seamless portability and high rendering performance across desktop and mobile devices.", "1. Presentation Layer (frontend/): "),
            ("p", "Exposed via FastAPI (Python 3.11), this layer enforces strict contract validation (Pydantic v2 schemas), asynchronous bounded streaming reads (64 KB chunks up to 25 MB max limit), prompt injection screening, and cross-origin resource sharing (CORS). It provides interactive OpenAPI documentation at `/docs`.", "2. API & Security Layer (app/api/, app/security/): "),
            ("p", "The `RAGQueryService` singleton caches retriever instances, vector store connections, BM25 indices, and pipeline components. It coordinates query execution, conversational routing, error handling, and transactional rollback during document ingestion.", "3. Service Orchestration Layer (app/services/): "),
            ("p", "Translates raw institutional files into structured intermediate representations. Contains format-specific loaders (`pypdf`, `python-docx`), conservative header/footer cleaners, modular regex structure detectors, and the `StructureAwareChunker`.", "4. Ingestion & Preprocessing Layer (ingestion/): "),
            ("p", "Executes multi-modal candidate selection by fan-out to a dense vector store (SQLite with 384-d vectors) and an inverted BM25 index. Merges candidates using Reciprocal Rank Fusion ($k=60$) and refines order via a deterministic cross-feature re-ranker.", "5. Multi-Channel Retrieval Layer (retrieval/): "),
            ("p", "Compiles retrieved evidence within a strict 1500-token budget ceiling and interfaces with a local Ollama daemon hosting Qwen3.5:4b. Handles thinking-block separation, raw `<think>` tag stripping, and low-temperature sampling (temperature=0.0).", "6. Neural Generation Layer (generation/): "),
            ("p", "Performs post-generation claim segmentation, entity containment validation (verifying exact dates, percentages, and course codes), and calculates Citation Precision and Recall before injecting clickable inline chips (`[1]`, `[2]`).", "7. Citation & Grounding Layer (citations/): "),
            ("p", "Manages raw files (`documents/raw/`), intermediate structured datasets (`documents/chunks/`), embedded SQLite database files (`data/vectorstore/sru_vectors.db`), and JSON inverted indices (`data/indices/bm25_index.json`).", "8. Persistent Storage Layer (data/, documents/): "),
            ("diagram", "diagram_02.png", "Figure 2: Component Interaction & Dataflow Diagram — End-to-end communication sequence."),
            ("heading_2", "2.3 Technology Stack & Runtime Specifications"),
            ("p", "The production technology stack was selected to prioritize operational autonomy, deterministic reproducibility, and zero external cloud subscription dependencies:", "Technology Profile: "),
            ("table", ["Component", "Technology / Framework", "Version / Spec", "Architectural Role"], [
                ["Runtime Language", "Python", "3.11.9 (64-bit)", "Core system execution environment"],
                ["Web Framework", "FastAPI", ">= 0.110.0", "Asynchronous REST API gateway & OpenAPI contracts"],
                ["ASGI Server", "Uvicorn", ">= 0.28.0", "Production HTTP server running on 0.0.0.0:8000"],
                ["Data Validation", "Pydantic & Pydantic-Settings", "v2.6+", "Strict schema parsing and environment configuration"],
                ["Vector Database", "SQLite 3", "3.45+ (Embedded)", "Embedded vector storage with 384-d BLOB cosine search"],
                ["Lexical Engine", "Okapi BM25", "Custom Python Core", "Persistent inverted index (k1=1.5, b=0.75, vocab=1387)"],
                ["LLM Daemon", "Ollama", "0.5.0+", "Local neural model execution server (localhost:11434)"],
                ["Active LLM Model", "Qwen3.5:4b", "4-Billion Params", "Grounded natural language answer generation"],
                ["Document Parsers", "pypdf & python-docx", "Latest Stable", "Text and table extraction across PDF, DOCX, and TXT"],
                ["Testing Framework", "pytest & pytest-cov", "pytest 9.0+", "326 automated unit, integration, and security tests"]
            ]),
            ("diagram", "diagram_03.png", "Figure 3: Technology Stack Diagram — Multi-layer library and database integration."),
            ("diagram", "diagram_04.png", "Figure 4: Repository Architecture — Module directory layout and file hierarchy."),
            ("page_break",)
        ]
    },
    {
        "id": "ch3",
        "title": "3. Document Ingestion, Parsing & Chunking Subsystem",
        "blocks": [
            ("heading_2", "3.1 Ingestion Pipeline Architecture"),
            ("p", "Document ingestion is orchestrated by `DocumentPipeline` (`ingestion/pipeline.py`), which converts raw academic files into clean, metadata-rich `ProcessedDocument` objects while maintaining strict provenance traceability. The ingestion lifecycle operates across four sequential stages: (1) Raw Extraction, (2) Cleaning and Normalization, (3) Modular Structure Detection, and (4) Metadata Extraction.", "Pipeline Execution: "),
            ("diagram", "diagram_05.png", "Figure 5: Official Document Upload & Ingestion Workflow — Upload, processing, and rollback."),
            ("heading_2", "3.2 Multi-Format Document Loaders"),
            ("p", "The `DocumentLoaderFactory` (`ingestion/loaders/factory.py`) dynamically resolves loaders based on file extensions:", "Loader Dispatch: "),
            ("p", "Utilizes `pypdf.PdfReader` to extract textual elements page-by-page. For each page, it captures raw text, records starting and ending character offsets, and assigns page provenance metadata (`page_number`, `source_file`, `extraction_timestamp`). Table text is flattened into sequential line blocks.", "PDF Loader (`ingestion/loaders/pdf_loader.py`): "),
            ("p", "Utilizes `python-docx` to inspect XML document structures. It extracts both standard paragraph elements and structured table grids. Tables are parsed cell-by-cell into atomic row elements, preserving structural associations between headers and data values.", "DOCX Loader (`ingestion/loaders/docx_loader.py`): "),
            ("p", "Loads plain text circulars and markdown syllabi using a robust fallback encoding cascade (`utf-8`, `utf-8-sig`, `latin-1`). This prevents encoding exceptions during bulk ingestion of historical circulars.", "TXT Loader (`ingestion/loaders/txt_loader.py`): "),
            ("diagram", "diagram_06.png", "Figure 6: Document Processing Pipeline Detail — Multi-stage transformation from raw file to intermediate IR."),
            ("heading_2", "3.3 Text Normalization & Structure Detection"),
            ("p", "The `DocumentCleaner` (`ingestion/processors/cleaner.py`) performs conservative text normalization. It strips non-printable control characters, standardizes Unicode quotation marks, and collapses whitespace. Crucially, it detects repeating headers and footers across document pages: any textual element appearing in identical positions on more than 80% of pages (`header_footer_threshold = 0.8`) is flagged and removed from the body text stream to prevent retrieval noise.", "Conservative Cleaning: "),
            ("p", "The `StructureDetector` (`ingestion/processors/structure_detector.py`) executes modular regex detector plugins:", "Entity Detection Plugins: "),
            ("p", "Matches patterns such as `23CS201PE408` or `CS301` to identify departmental courses.", "• CourseCodeDetector: "),
            ("p", "Identifies specific regulation frameworks such as `R23`, `R20`, or `R18`.", "• RegulationDetector: "),
            ("p", "Extracts formal assessment milestones (e.g., 'Mid-Semester Examination I', 'End Semester Exams').", "• ExaminationDetector: "),
            ("p", "Extracts calendar milestones and deadlines using calendar-specific date formats.", "• DateDetector: "),
            ("heading_2", "3.4 Structure-Aware Chunking Strategy"),
            ("p", "Conventional fixed-window chunkers cut text arbitrarily at fixed character boundaries, frequently severing table rows, mid-sentence definitions, or heading-paragraph associations. SRU Assistant implements `StructureAwareChunker` (`ingestion/chunking/structure_aware.py`), which strictly prioritizes semantic and structural boundaries according to a strict hierarchy: Heading Level 1 -> Heading Level 2 -> Table/List -> Paragraph -> Sentence -> Token.", "Boundary Preservation: "),
            ("p", "Configuration parameters are enforced via `Settings` (`app/config/settings.py`): Target Chunk Size: 500 tokens; Chunk Overlap: 100 tokens; Minimum Chunk Size: 50 tokens (to prevent orphaned fragments); Maximum Hard Ceiling: 1200 tokens (forcing clean sentence splits if a single paragraph exceeds token limits).", "Chunking Hyperparameters: "),
            ("p", "Every chunk produced by `StructureAwareChunker` inherits the complete hierarchical path of parent headings (e.g., `Academic Regulations -> Section 4 -> Attendance Rules`). Furthermore, local academic entities detected within the chunk boundary are cataloged directly into `ChunkMetadata`, enabling downstream soft metadata filtering during retrieval.", "Section Path Inheritance: "),
            ("diagram", "diagram_07.png", "Figure 7: Structure-Aware Chunking & Metadata Flow — Semantic boundary preservation and hierarchy inheritance."),
            ("page_break",)
        ]
    },
    {
        "id": "ch4",
        "title": "4. Dual-Store Indexing, Storage Architecture & Rollback",
        "blocks": [
            ("heading_2", "4.1 Dual-Store Indexing Strategy"),
            ("p", "SRU Assistant maintains dual, synchronized indexing stores: an embedded SQLite vector store for dense semantic retrieval and a persistent JSON inverted index for Okapi BM25 lexical retrieval. Both stores index the exact same set of 43 structured chunks derived from official university documents (curricula, regulations, academic calendars, and circulars).", "Dual-Channel Philosophy: "),
            ("diagram", "diagram_08.png", "Figure 8: Embedding & Indexing Architecture — Simultaneous registration into dense vector and lexical BM25 indices."),
            ("heading_2", "4.2 SQLite Vector Store Schema"),
            ("p", "The SQLite vector store (`data/vectorstore/sru_vectors.db`) is managed by `SQLiteVectorStore` (`retrieval/vectorstore/sqlite_store.py`). The database schema contains two primary tables:", "Relational Schema: "),
            ("table", ["Column Name", "Data Type", "Constraints", "Description"], [
                ["id", "INTEGER", "PRIMARY KEY CHECK(id=1)", "Singleton index manifest identifier"],
                ["embedding_provider", "TEXT", "NOT NULL", "Provider name ('fasthash' or 'ollama')"],
                ["embedding_model", "TEXT", "NOT NULL", "Model identifier ('fasthash-384')"],
                ["embedding_dimension", "INTEGER", "NOT NULL", "Vector dimension (384)"],
                ["distance_metric", "TEXT", "NOT NULL", "Distance metric ('cosine')"],
                ["index_version", "TEXT", "NOT NULL", "Index schema version ('1.0.0')"],
                ["created_at", "TEXT", "NOT NULL", "ISO-8601 creation timestamp"],
                ["total_vectors", "INTEGER", "NOT NULL", "Total indexed chunks count (43)"]
            ]),
            ("p", "Table 2: Schema definition for `index_manifest` in `sru_vectors.db`.", ""),
            ("table", ["Column Name", "Data Type", "Constraints", "Description"], [
                ["chunk_id", "TEXT", "PRIMARY KEY", "Unique chunk tracking identifier"],
                ["document_id", "TEXT", "NOT NULL", "Foreign reference to parent document"],
                ["text", "TEXT", "NOT NULL", "Complete textual content of the chunk"],
                ["chunk_content_hash", "TEXT", "NOT NULL", "SHA-256 hash of chunk text"],
                ["vector", "BLOB", "NOT NULL", "Binary packed float32 vector array"],
                ["metadata_json", "TEXT", "NOT NULL", "Serialized chunk metadata and section hierarchy"],
                ["provenance_json", "TEXT", "NOT NULL", "Serialized page and file provenance data"],
                ["department", "TEXT", "NULLABLE", "Indexed metadata: Department (e.g. 'CSE')"],
                ["semester", "TEXT", "NULLABLE", "Indexed metadata: Semester (e.g. 'VII')"],
                ["regulation", "TEXT", "NULLABLE", "Indexed metadata: Regulation (e.g. 'R23')"],
                ["academic_year", "TEXT", "NULLABLE", "Indexed metadata: Academic Year ('2026-27')"],
                ["created_at", "TEXT", "NOT NULL", "Insertion timestamp"]
            ]),
            ("p", "Table 3: Schema definition for `vector_records` in `sru_vectors.db`. B-Tree indices exist on `document_id`, `department`, `semester`, `regulation`, and `academic_year`.", ""),
            ("diagram", "diagram_09.png", "Figure 9: Vector Database & BM25 Storage Layout — Physical file structure and table organization."),
            ("heading_2", "4.3 Transactional Rollback Safeguard"),
            ("p", "Document ingestion is a multi-stage operation. If an unhandled exception occurs during vector embedding generation or BM25 index updating, partial records could corrupt the dual-store synchronization, leaving ghost entries or mismatched chunk IDs. To eliminate this vulnerability, `RAGQueryService.ingest_and_index_file()` (`app/services/query_service.py`) wraps ingestion in a strict multi-stage transactional rollback block:", "Atomic Recovery: "),
            ("callout", "When any ingestion stage fails (load, clean, chunk, vector index, or BM25 index), the system triggers a 4-tier rollback: (1) Purges inserted chunk terms from the BM25 index and flushes the clean index file to disk; (2) Executes `DELETE FROM vector_records WHERE chunk_id IN (...)` in SQLite; (3) Unlinks intermediate chunk and processed JSON files; (4) Unlinks the uploaded raw document from `documents/raw/`. Failed indexing never leaves orphaned artifacts.", "TRANSACTIONAL INTEGRITY GUARANTEE"),
            ("page_break",)
        ]
    },
    {
        "id": "ch5",
        "title": "5. Embedding Subsystem & Vector Similarity Search",
        "blocks": [
            ("heading_2", "5.1 Embedding Interface & Factory Pattern"),
            ("p", "The embedding subsystem (`retrieval/embeddings/`) provides a decoupled abstraction layer for vector representations. The base class `BaseEmbeddingModel` defines two abstract methods: `embed_query(text: str) -> list[float]` and `embed_documents(texts: list[str]) -> list[list[float]]`. The `get_embedding_model()` factory resolves the configured provider based on `Settings.embedding_provider`.", "Embedder Decoupling: "),
            ("diagram", "diagram_10.png", "Figure 10: Embedding Generation Workflow — Deterministic FastHash vs Neural Ollama embedding pipelines."),
            ("heading_2", "5.2 FastHash-384 Deterministic Baseline"),
            ("p", "The default operational provider in the repository is `FastHashEmbeddingModel` (`retrieval/embeddings/fast_hash.py`). FastHash is a deterministic lexical-semantic hashing model designed for instant offline execution, CI testing, and evaluation reproducibility. It projects text into a 384-dimensional dense float vector by hashing character n-grams and token subspaces using salted SHA-256 digests:", "Deterministic Architecture: "),
            ("p", "Each token is hashed into multiple subspace buckets, accumulating signed weights in the vector. Once accumulated, the vector is scaled to unit length via Euclidean $L_2$ normalization: $V_{norm} = \\frac{V}{\\|V\\|_2}$. FastHash requires zero external GPU memory, zero network roundtrips, and produces identical vector embeddings across Windows, Linux, and macOS environments.", "Subspace Projection: "),
            ("heading_2", "5.3 Neural Ollama Embeddings Integration"),
            ("p", "For deep semantic embeddings, `OllamaEmbeddingModel` (`retrieval/embeddings/ollama.py`) connects to a local Ollama daemon via HTTP POST `/api/embeddings`. It supports transformer-based embedding backends such as `nomic-embed-text` or `all-minilm`. When enabled, it captures rich contextual semantics, cross-lingual synonymy, and paraphrase similarity.", "Neural Integration: "),
            ("heading_2", "5.4 SQLite Vector Scanning & Cosine Distance"),
            ("p", "Vector similarity search is executed by `SQLiteVectorStore.similarity_search()` (`retrieval/vectorstore/sqlite_store.py`). Vectors are stored in SQLite as binary BLOBs using Python's `struct.pack('384f', *vector)`. During query execution:", "Search Mathematics: "),
            ("p", "1. The user query is encoded into a unit-normalized 384-dimensional float query vector $Q$.\n2. SQLite executes an indexed query to scan candidate records matching any active hard metadata filters.\n3. Binary BLOBs are unpacked in memory using `struct.unpack('384f', blob)`.\n4. Cosine similarity is computed via dot product: $Sim(Q, D) = Q \\cdot D = \\sum_{i=1}^{384} Q_i D_i$.\n5. Candidates are sorted in descending order of similarity score, breaking ties by `chunk_id` ASC to ensure complete deterministic repeatability.", "Similarity Scanning: "),
            ("diagram", "diagram_11.png", "Figure 11: SQLite Vector Storage & Search Architecture — Binary BLOB unpacking and cosine scoring."),
            ("page_break",)
        ]
    },
    {
        "id": "ch6",
        "title": "6. Lexical BM25 Engine & Reciprocal Rank Fusion",
        "blocks": [
            ("heading_2", "6.1 Okapi BM25 Mathematical Mechanics"),
            ("p", "While dense vector embeddings excel at semantic similarity ('what are the rules for missing exams'), they struggle with exact alphanumeric codes, course identifiers (e.g., `23CS201PE408`), regulation versions (`R23`), and specific dates. To guarantee exact keyword recall, SRU Assistant integrates a persistent Okapi BM25 lexical search engine (`retrieval/lexical/bm25.py`).", "Lexical Recall Need: "),
            ("p", "The BM25 score for a document $D$ given query $Q$ containing tokens $q_1, q_2, \\dots, q_n$ is computed as:", "BM25 Equation: "),
            ("p", "Score(D, Q) = \\sum_{i=1}^n \\text{IDF}(q_i) \\cdot \\frac{f(q_i, D) \\cdot (k_1 + 1)}{f(q_i, D) + k_1 \\cdot \\left(1 - b + b \\cdot \\frac{|D|}{\\text{avgdl}}\\right)}", "Formula: "),
            ("p", "Where $f(q_i, D)$ is the term frequency of token $q_i$ in chunk $D$, $|D|$ is the token length of chunk $D$, $\\text{avgdl}$ is the average chunk length across the index (106.95 tokens in our catalog), $k_1 = 1.5$ is the term frequency saturation parameter, and $b = 0.75$ controls document length normalization.", "Parameter Definitions: "),
            ("p", "Inverse Document Frequency (IDF) is calculated using the standard Robertson-Spärck Jones formula:", "IDF Formulation: "),
            ("p", "\\text{IDF}(q_i) = \\ln\\left( \\frac{N - n(q_i) + 0.5}{n(q_i) + 0.5} + 1 \\right)", "Formula: "),
            ("p", "Where $N = 43$ is the total number of indexed chunks, and $n(q_i)$ is the number of chunks containing token $q_i$. The BM25 inverted index (`data/indices/bm25_index.json`) maintains 1,387 distinct vocabulary postings.", "Index Stats: "),
            ("diagram", "diagram_12.png", "Figure 12: Okapi BM25 Retrieval Workflow — Tokenization, posting lookup, and scoring mechanics."),
            ("heading_2", "6.2 Reciprocal Rank Fusion (RRF) Formulation"),
            ("p", "A fundamental challenge in hybrid search is reconciling incompatible score scales: dense cosine similarity is bounded in $[-1, 1]$ (or $[0, 1]$ for normalized text), whereas BM25 scores are unbounded $[0, \\infty)$ and vary drastically based on query length and rare term frequencies. Directly normalizing and adding these scores causes calibration drift.", "Scale Incompatibility: "),
            ("p", "SRU Assistant bypasses score calibration by implementing Reciprocal Rank Fusion (`retrieval/fusion/rrf.py`). RRF discards raw scores and aggregates candidates purely on their ordinal positions in the respective ranked lists:", "Rank Consensus: "),
            ("p", "\\text{RRF}(d) = \\sum_{m \\in \\{\\text{dense}, \\text{lexical}\\}} \\frac{w_m}{k + \\text{rank}_m(d)}", "Formula: "),
            ("p", "Where $k = 60$ is the standard smoothing constant preventing top-ranked items from dominating disproportionately, $\\text{rank}_m(d)$ is the 1-indexed position of chunk $d$ in modality $m$, and $w_m = 1.0$ is the modality weight.", "Smoothing Parameters: "),
            ("diagram", "diagram_13.png", "Figure 13: Hybrid Retrieval Architecture — Dual-channel search fan-out and RRF merge."),
            ("diagram", "diagram_14.png", "Figure 14: Reciprocal Rank Fusion Flowchart & Worked Example — Consensus ranking mechanism."),
            ("heading_2", "6.3 Empirical Hybrid Search Performance Gains"),
            ("p", "Empirical evaluations conducted on the project's 16-query benchmark suite demonstrate the superiority of Hybrid RRF over single-channel Dense search:", "Empirical Verification: "),
            ("table", ["Retrieval Modality", "Recall@1", "Recall@3", "Recall@5", "MRR (Mean Reciprocal Rank)", "nDCG@5"], [
                ["Experiment A: Dense Vector Only", "0.3438", "0.7188", "0.7188", "0.5625", "0.5718"],
                ["Experiment B: Hybrid RAG (Dense + BM25 RRF)", "0.5000", "0.7812", "0.8125", "0.6719", "0.6859"],
                ["Experiment C: Hybrid + Cross-Feature Re-ranking", "0.5625", "0.7812", "0.8125", "0.7083", "0.7191"]
            ]),
            ("p", "Table 4: Empirical benchmark evaluation results from `data/benchmarks/rag_evaluation_report.json`. Hybrid RRF increases Recall@5 by +9.37 percentage points and MRR by +0.1094 over Dense-only retrieval.", ""),
            ("page_break",)
        ]
    }
]

print("Chapters 1 through 6 data defined.")
