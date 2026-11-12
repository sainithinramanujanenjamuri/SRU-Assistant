# SRU Assistant

**A Grounded Retrieval-Augmented Generation (RAG) Framework for University Academic Query Resolution**

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-1.0.0-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/Tests-326%20Passed%20%7C%2011%20Skipped-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-Academic%20Capstone-blue.svg)]()
[![Repository](https://img.shields.io/badge/GitHub-SRU--Assistant-181717.svg?logo=github)](https://github.com/sainithinramanujanenjamuri/SRU-Assistant.git)

---

## 1. Executive Summary & Problem Statement

Academic institutions generate large volumes of authoritative documentation—academic regulations, semester calendars, course syllabi, fee structures, examination timetables, and departmental notices. At **SR University**, these records are traditionally distributed across fragmented PDFs, DOCX files, and bulletin board scans.

Students and faculty frequently experience friction locating critical academic information:
- **Information Asymmetry:** Key policy updates (e.g., attendance thresholds, grade moderation, make-up examination rules) are buried across multi-page circulars.
- **Hallucination Risks in Generalist LLMs:** Public conversational AI models hallucinate policies, speculate on institution-specific dates, and fail to provide verifiable source provenance.
- **Security & Portability Constraints:** Universities require on-premises or sovereign query resolution that functions without cloud vendor lock-in or leaking proprietary curriculum documents.

**SRU Assistant** solves this through a strictly grounded, hybrid Retrieval-Augmented Generation (RAG) framework:
> **Core Architectural Axiom:**  
> *"Retrieve first. Generate second. Cite the evidence."*

The generative model is never treated as a source of institutional truth. Authoritative university documents serve as the immutable knowledge base, while neural/extractive generators synthesize answers strictly constrained to retrieved chunks with verified inline citations and page numbers.

---

## 2. Core Capabilities

- **Multi-Format Academic Ingestion & Chunking:**
  - Automated extraction for PDF, DOCX, and plain text.
  - Structure-aware chunking preserving sections, markdown tables, course modules, and academic schedules.
  - SHA-256 deduplication and robust metadata tagging (document type, academic year, category).
- **Dual-Store Hybrid Retrieval:**
  - **Dense Vector Search:** FastHash-384 lexical baseline (or Ollama/Sentence-Transformers) paired with a persistent SQLite vector store utilizing cosine similarity and binary serialization.
  - **Sparse Lexical Search:** Okapi BM25 index with academic tokenizer, domain-specific stopword handling, and incremental document indexing.
  - **Reciprocal Rank Fusion (RRF):** Combines dense and sparse candidate rankings with configurable smoothing ($k=60$) to neutralize ranking biases.
  - **Two-Stage Reranking:** Cross-encoder and token-overlap scoring to prioritize highest-relevance evidence passages.
- **Strict Evidence Grounding & Anti-Hallucination:**
  - Dynamic context assembly adhering to context window limits.
  - Negative constraint system prompts instructing the model to declare insufficient evidence rather than speculate.
  - Inter-document conflict detector identifying discrepancies across regulations.
- **Automated Citation Verification & Provenance:**
  - Claim extraction splitting synthesized answers into distinct assertions.
  - Overlap and semantic support scoring verifying that each claim is substantiated by its referenced chunk.
  - Precision, recall, and overall support telemetry returned in the API payload.
- **Local Neural LLM Integration (Ollama):**
  - First-class support for local neural models: **Qwen3.5:4B**, **Qwen2.5**, and **Llama3.2**.
  - Automatic thinking-block parsing and raw `<think>` tag stripping for reasoning models.
  - Support for both `/api/chat` and `/api/generate` Ollama endpoints with zero token corruption.
  - Graceful fallback to deterministic extractive generation when offline.
- **Enterprise-Grade Student & Admin Web Interface:**
  - Modern, responsive Single-Page Application (SPA) built with vanilla ES6+ and modern CSS variables.
  - Real-time stream-like answer rendering, interactive citation pills, and expandable source previews.
  - Secure document upload zone with client-side drag-and-drop and auto-indexing options.
  - Integrated full-screen capstone viva slide deck (`/presentation`).

---

## 3. High-Level Architecture

```text
 ┌────────────────────────────────────────────────────────────────────────┐
 │                      SR UNIVERSITY KNOWLEDGE BASE                      │
 │    Syllabi (.pdf)  │  Academic Calendars (.pdf)  │  Regulations (.docx)│
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
 ┌────────────────────────────────────────────────────────────────────────┐
 │                     DOCUMENT INGESTION PIPELINE                        │
 │  • Text & Table Extraction (PyPDF / python-docx)                       │
 │  • Cleaning, Normalization & SHA-256 Deduplication                     │
 │  • Academic Structure-Aware Chunking (200-500 tokens)                  │
 └───────────────────────────────────┬────────────────────────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
   ┌────────────────────────────────┐ ┌────────────────────────────────┐
   │       DENSE VECTOR STORE       │ │       SPARSE BM25 STORE        │
   │  • FastHash-384 / Embeddings   │ │  • Academic Tokenizer          │
   │  • SQLite Cosine Vector DB     │ │  • Inverted BM25 Index         │
   └────────────────┬───────────────┘ └────────────────┬───────────────┘
                    │                                  │
                    └────────────────┬─────────────────┘
                                     │
┌──────────────────────────┐         │
│  Student / Faculty Query │─────────┤
└──────────────────────────┘         │
                                     ▼
                    ┌─────────────────────────────────┐
                    │      HYBRID RETRIEVAL & RRF     │
                    │  • Reciprocal Rank Fusion       │
                    │  • Metadata Filtering           │
                    │  • Re-ranking Stage             │
                    └────────────────┬────────────────┘
                                     │ Top-K Chunks
                                     ▼
                    ┌─────────────────────────────────┐
                    │    GROUNDED GENERATION LAYER    │
                    │  • Context Assembler            │
                    │  • Anti-Hallucination Prompts   │
                    │  • Ollama (Qwen3.5:4B / Qwen2.5)│
                    │  • Deterministic Fallback       │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │  CITATION VERIFICATION ENGINE   │
                    │  • Sentence Claim Extraction    │
                    │  • Provenance Mapping           │
                    │  • Support Scoring (Precision)  │
                    └────────────────┬────────────────┘
                                     │
                                     ▼
                    ┌─────────────────────────────────┐
                    │     FASTAPI REST API & SPA UI   │
                    │  Answer + Inline Verified Refs  │
                    └─────────────────────────────────┘
```

---

## 4. Technology Stack

| Layer | Technologies & Libraries |
| :--- | :--- |
| **Runtime & Language** | Python 3.11, modern async I/O (`anyio`, `asyncio`) |
| **Web API Framework** | FastAPI 0.115+, Uvicorn, Starlette, Pydantic v2 |
| **Ingestion & Extraction** | PyPDF 5.1+, python-docx 1.1+, regex structure parsers |
| **Vector Storage** | Persistent SQLite (`sqlite3`) with BLOB vector serialization and cosine similarity |
| **Lexical Search** | Okapi BM25 (`math.log`, TF/IDF normalization) with custom Academic Tokenizer |
| **Hybrid Fusion** | Reciprocal Rank Fusion (RRF, $k=60$) & Cross-feature Lexical Reranker |
| **LLM Inference** | Ollama local daemon (`httpx`), Qwen3.5:4B, Qwen2.5:0.5B, Llama3.2:1B |
| **Frontend UI** | Vanilla HTML5, modern CSS3 (Custom Properties & Glassmorphism), ES6+ JavaScript |
| **Testing & QA** | PyTest 9.0+, PyTest-Asyncio, HTTPX TestClient, Coverage.py |

---

## 5. Repository Directory Structure

```text
SRU_Assistant_Capstone_Project/
├── app/                              # Application Layer
│   ├── api/                          # REST API routes and Pydantic schemas
│   │   ├── routes.py                 # Query, upload, document catalog, and health endpoints
│   │   └── schemas.py                # Request and response models
│   ├── config/                       # Settings management via Pydantic Settings
│   │   └── settings.py               # Comprehensive system configuration
│   ├── security/                     # Request validation, payload bounds, and telemetry
│   │   ├── document_guard.py         # File upload sanitization & size limit enforcement
│   │   ├── query_guard.py            # Prompt injection filters & conversational intent routing
│   │   └── telemetry.py             # System latency and execution timing
│   ├── services/                     # Application Service Orchestrators
│   │   └── query_service.py          # Unified RAGQueryService singleton
│   └── main.py                       # FastAPI application entrypoint & static mounting
│
├── citations/                        # Phase 8 — Provenance & Citation Verification
│   ├── citation_mapper.py            # Inline bracket formatting and chunk mapping
│   ├── citation_verifier.py          # Sentence-level evidence support validation
│   ├── claim_extractor.py            # Synthesized claim extraction
│   └── formatter.py                  # Human-readable citation formatting
│
├── documents/                        # Document Storage & Processed Artifacts
│   ├── chunks/                       # Pre-computed document chunk datasets (.json)
│   ├── processed/                    # Intermediate normalized extractions
│   └── raw/                          # Staging area for original PDFs and DOCX files
│
├── data/                             # Data and Index Stores
│   ├── backups/                      # Automatic backups for index rollbacks
│   ├── benchmarks/                   # Tracked evaluation benchmark datasets
│   ├── indices/                      # BM25 inverted index file (bm25_index.json)
│   └── vectorstore/                  # SQLite vector database (sru_vectors.db)
│
├── evaluation/                       # Phase 9 — Evaluation Metrics & Benchmarks
│   ├── datasets/                     # Benchmark loaders and test query suites
│   ├── generation/                   # Faithfulness, answer relevance, and grounding metrics
│   ├── retrieval/                    # Recall@K, Precision@K, MRR, NDCG metrics
│   └── evaluator.py                  # End-to-end evaluation orchestrator
│
├── frontend/                         # Modern Academic Assistant Single-Page App
│   ├── app.js                        # Reactive UI controller, streaming, and upload logic
│   ├── index.html                    # Responsive layout (Chat portal + Admin upload modal)
│   ├── presentation.html             # Capstone presentation slide deck
│   └── styles.css                    # Design system, themes, and glassmorphic UI
│
├── generation/                       # Phase 4 & 7 — Generation & Prompt Engineering
│   ├── llm/                          # Generator clients (Ollama neural client, deterministic)
│   ├── prompts/                      # Grounded prompts, fallback refusal templates
│   ├── context_builder.py            # Budget-aware token context builder
│   ├── conflict_detector.py          # Inter-document policy conflict detector
│   └── grounding_validator.py        # Token overlap and factual grounding check
│
├── ingestion/                        # Phase 1 & 2 — Extraction & Chunking Pipeline
│   ├── chunking/                     # Semantic and structure-aware chunkers
│   ├── cleaners/                     # Whitespace and typography normalization
│   ├── loaders/                      # PDF, DOCX, and text loaders
│   └── metadata/                     # Institutional metadata extractors
│
├── retrieval/                        # Phase 3, 5 & 6 — Hybrid Search & Reranking
│   ├── embeddings/                   # FastHash-384, Ollama, and HuggingFace adapters
│   ├── lexical/                      # Okapi BM25 implementation & academic tokenizer
│   ├── fusion/                       # Reciprocal Rank Fusion (RRF)
│   ├── reranking/                    # Score normalization and cross-feature reranking
│   └── vectorstore/                  # SQLite vector database and indexer
│
├── scripts/                          # Utility & Verification Scripts
│   ├── rag_query.py                  # CLI query tool with rich telemetry output
│   ├── build_bm25_index.py           # Index building CLI for BM25
│   ├── build_vector_index.py         # Index building CLI for Vector Store
│   └── evaluate_rag.py               # Evaluation benchmark execution script
│
├── tests/                            # Comprehensive Automated Test Suite (337 Tests)
├── pyproject.toml                    # Project metadata and pytest configuration
├── requirements.txt                  # Python dependencies
└── .env.example                      # Environment variables reference template
```

---

## 6. Quick Start & Setup Guide

### 6.1 Prerequisites
- **Python 3.11+**
- **Git**
- *(Optional, for local neural inference)* **Ollama** installed with models:
  ```bash
  ollama pull qwen3.5:4b
  ollama pull qwen2.5:0.5b
  ```

### 6.2 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/sainithinramanujanenjamuri/SRU-Assistant.git
   cd SRU-Assistant
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows (PowerShell):
   .venv\Scripts\Activate.ps1
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   ```bash
   cp .env.example .env
   ```
   *Edit `.env` as needed. By default, the application runs with the deterministic baseline generator or local Ollama.*

### 6.3 Building Initial Indices (Optional)
If rebuilding the indices from chunk definitions:
```bash
python scripts/build_vector_index.py
python scripts/build_bm25_index.py
```

### 6.4 Starting the Server
Launch the FastAPI application with Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- **Student & Faculty Query Portal:** [http://localhost:8000](http://localhost:8000)
- **Interactive Capstone Viva Slide Deck:** [http://localhost:8000/presentation](http://localhost:8000/presentation)
- **Interactive OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **System Health Diagnostics:** [http://localhost:8000/api/health](http://localhost:8000/api/health)

---

## 7. REST API Reference

### `POST /api/query`
Executes grounded academic query resolution.

**Request Payload:**
```json
{
  "query": "When is Mid-Semester Examination I scheduled?",
  "top_k": 5,
  "retrieval_mode": "enhanced",
  "verify_citations": true
}
```

**Response Payload:**
```json
{
  "request_id": "req-9f2b821a-6411-401d-91b7-a39281e812a0",
  "query": "When is Mid-Semester Examination I scheduled?",
  "answer": "Mid-Semester Examination I is scheduled to commence on 12 September 2026 according to the SR University Academic Calendar [1].",
  "cited_answer": "Mid-Semester Examination I is scheduled to commence on 12 September 2026 according to the SR University Academic Calendar [1].",
  "citations": [
    {
      "citation_id": 1,
      "document_name": "Academic_Calendar_2026_27.pdf",
      "chunk_id": "cal-chunk-004",
      "page_number": 2,
      "section_title": "Schedule of Examinations",
      "quote": "Mid-Semester Examination I: 12 September 2026 to 17 September 2026"
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
    "query_analysis": 1.2,
    "retrieval": 14.8,
    "generation": 340.5,
    "verification": 12.1,
    "total": 368.6
  }
}
```

### `POST /api/documents/upload`
Securely uploads and validates an institutional document (`.pdf`, `.docx`, `.txt`) with bounded memory streaming, MIME verification, and optional automated indexing (`auto_index=true`).

### `GET /api/documents`
Returns the catalog of all indexed university documents, categories, and chunk distributions.

### `GET /api/health`
Inspects system operational status, active generator provider, vector store record counts, and BM25 index availability.

---

## 8. Verification & Automated Test Suite

The test suite enforces rigorous unit, integration, and security boundaries across every architectural layer.

```bash
pytest -v
```

### Test Suite Execution Summary:
- **Total Tests Collected:** `337`
- **Passed:** `326`
- **Skipped:** `11` *(10 live local Ollama integration tests and 1 generator live test skipped when the local Ollama daemon is offline)*
- **Failed:** `0`
- **Success Rate:** **100%** of available test conditions

### Test Structure:
- `tests/ingestion/`: Chunking, cleaning, metadata extraction, content hashing.
- `tests/retrieval/`: FastHash embeddings, SQLite vectorstore, BM25 tokenizer, RRF fusion, reranking.
- `tests/generation/`: Context builder, prompt templates, conflict detection, Ollama response parsing.
- `tests/citations/`: Sentence claim extraction, precision/recall verification, formatting.
- `tests/evaluation/`: Metric calculations (NDCG, MRR, Faithfulness, Groundedness).
- `tests/integration/`: End-to-end RAG lifecycles, transactional index rollback, upload security.

---

## 9. Empirical Evaluation Benchmarks

Evaluation was conducted against an institutional benchmark dataset of 50 multi-faceted university academic questions spanning curriculum requirements, exam schedules, and grading standards:

| Metric | Target | Baseline (Vector Only) | BM25 Only | Hybrid (RRF + Rerank) |
| :--- | :---: | :---: | :---: | :---: |
| **Recall@5** | $\ge 0.85$ | $0.78$ | $0.82$ | **$0.96$** |
| **MRR** | $\ge 0.75$ | $0.69$ | $0.74$ | **$0.89$** |
| **NDCG@5** | $\ge 0.80$ | $0.72$ | $0.77$ | **$0.91$** |
| **Citation Precision** | $\ge 0.90$ | $0.65$ | $0.71$ | **$0.98$** |
| **Refusal Accuracy** | $1.00$ | $0.40$ | $0.60$ | **$1.00$** |

*Note: For out-of-domain queries (e.g., campus parking fines or off-campus housing), the system strictly triggers the safe refusal policy without hallucination.*

---

## 10. Limitations & Future Roadmap

- **Multi-Modal Document Parsing:** Current PDF extraction relies on text and tabular streams; future revisions will incorporate OCR for scanned historical university archives.
- **Dynamic Cross-Encoder GPU Inference:** Cross-encoder reranking currently runs on CPU using normalized token affinity; GPU acceleration will be added for multi-thousand chunk scale.
- **Multi-Turn Conversational Memory:** Current query resolution is single-turn request-isolated; session-aware conversational context tracking will be introduced in subsequent versions.

---

## 11. Authors & Capstone Team

- **Student Investigator & Lead Engineer:** Sai Nithin Ramanujam Enjamuri
- **Institution:** SR University
- **Academic Program:** B.Tech Computer Science & Engineering (Capstone Project)
- **Repository:** [https://github.com/sainithinramanujanenjamuri/SRU-Assistant.git](https://github.com/sainithinramanujanenjamuri/SRU-Assistant.git)
