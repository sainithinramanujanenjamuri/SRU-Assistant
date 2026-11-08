# Architecture Walkthrough: SRU Assistant

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  
**Document Purpose:** Comprehensive architectural and engineering reference for university evaluation and developer onboarding  

---

## 1. System Mission & Core Tenets

**SRU Assistant** is an institutional academic query resolution framework developed for SR University. University academic inquiries (such as grading policies, exam schedules, attendance minimums, course prerequisites, and credit regulations) demand zero tolerance for hallucination. A false policy citation directly harms students and institutional compliance.

### Three Non-Negotiable Core Tenets:
1. **Strict Non-Fabrication:** If evidence is absent, the system explicitly refuses with a verified fallback message. It never guesses or extrapolates.
2. **Deterministic Provenance:** Every claim is bound to an exact document name, page number, line range, and immutable chunk content hash.
3. **Local & Lightweight Portability:** Runs in standard CPU-only environments without mandatory paid API keys or dedicated GPU hardware, while seamlessly accommodating local neural models (e.g. Ollama).

---

## 2. End-to-End Information Flow

```
[Institutional Document (.pdf, .docx, .txt)]
                    │
                    ▼
       ┌────────────────────────┐
       │ Ingestion Pipeline     │
       │  • Magic byte check    │
       │  • Header/footer strip │
       │  • Academic detection  │
       └────────────┬───────────┘
                    ▼
       ┌────────────────────────┐
       │ Structure-Aware        │
       │ Chunking               │
       │  • Heading breadcrumbs │
       │  • Table markdown      │
       │  • Overlap & token cap │
       └────────────┬───────────┘
                    ▼
         Dual-Channel Storage
        ┌───────────┴───────────┐
        ▼                       ▼
┌──────────────────┐    ┌─────────────────┐
│ SQLite Vector DB │    │ BM25 Inverted   │
│ (384-d FastHash) │    │ Posting Index   │
└────────┬─────────┘    └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
       ┌────────────────────────┐
       │ Hybrid RRF Fusion      │
       │  • RRF (k=60)          │
       │  • Top-20 + Top-20     │
       └────────────┬───────────┘
                    ▼
       ┌────────────────────────┐
       │ Enhancement & Rerank   │
       │  • Metadata filter     │
       │  • Entity reranker     │
       └────────────┬───────────┘
                    ▼
       ┌────────────────────────┐
       │ Grounded Prompt &      │
       │ Conflict Detection     │
       │  • Token bounding      │
       │  • Conflict scan       │
       └────────────┬───────────┘
                    ▼
       ┌────────────────────────┐
       │ Generation (LLM / Rule)│
       │  • Deterministic/Ollama│
       └────────────┬───────────┘
                    ▼
       ┌────────────────────────┐
       │ Audit & Provenance     │
       │  • Claim extraction    │
       │  • N-gram overlap      │
       │  • Citation verifier   │
       └────────────┬───────────┘
                    ▼
             [Student Portal UI]
```

---

## 3. Detailed Component Deep-Dive

### 3.1 Ingestion & Document Intelligence (`ingestion/`)
- **Loaders:** `PDFLoader` (extracts text with `pypdf`, preserving page numbers), `DOCXLoader` (extracts paragraphs and structured tables), and `TXTLoader` (line tracking with multi-encoding fallbacks: UTF-8, UTF-8-BOM, Latin-1).
- **Cleaners:** `DocumentCleaner` suppresses repeating headers and footers that distort lexical retrieval.
- **Academic Detectors:** Regex and rule detectors identify Course Codes (`23CSE302T`), Regulations (`R23`), Academic Years (`2026-27`), Semesters, and Dates.

### 3.2 Chunking & Provenance (`ingestion/chunking/`)
- **`StructureAwareChunker`:** Maintains heading hierarchies so that nested sections (e.g., `Syllabus > Unit III > Graph Theory`) retain contextual identity even when split across chunks.
- **Table Preservation:** Markdown tables are preserved as whole chunks rather than broken mid-row.
- **Provenance:** Every chunk stores `ChunkProvenance` with `document_id` (SHA-256), `source_file`, `page_numbers`, `line_numbers`, and `element_ids`.

### 3.3 Retrieval Engine (`retrieval/`)
- **Dense Channel:** `VectorRetriever` queries `SQLiteVectorStore` storing float32 embeddings. Default `fasthash` generates deterministic 384-dimensional vectors.
- **Lexical Channel:** `BM25Retriever` uses `AcademicTokenizer` to preserve hyphenated terms, course codes, and abbreviations.
- **Fusion:** `HybridRetriever` implements Reciprocal Rank Fusion ($k=60$) combining top candidates from both channels.
- **Re-ranking:** `DeterministicCrossFeatureReranker` boosts candidates with exact course code matches, regulation alignment, and heading matches.

### 3.4 Generation, Grounding & Citations (`generation/`, `citations/`)
- **`ContextBuilder`:** Enforces token bounds (`rag_context_max_tokens = 1500`) and tags evidence with `<evidence id='X'>`.
- **`ConflictDetector`:** Flags discrepancies when multiple institutional documents cite differing dates or regulations.
- **`GroundingValidator`:** Computes token overlap and n-gram containment between generated assertions and evidence.
- **`CitationVerifier`:** Maps citations (`[1]`, `[2]`) to source chunks and scores textual support.

### 3.5 API & Security Layer (`app/`)
- **FastAPI:** Clean separation of schemas, routes, services, and security.
- **`QueryGuard`:** Protects against prompt injection, jailbreaking, and input flooding.
- **`DocumentGuard`:** Magic bytes validation, file size bounds (10B to 25MB), and traversal sanitization.
- **`ObservabilityLogger`:** Structured telemetry logging per request with randomized IDs (`req_...`).

