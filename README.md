# SRU Assistant

**A RAG Framework for University Academic Query Resolution**

---

## 1. Overview

**SRU Assistant** is an academic question-answering framework designed to provide students and faculty at SR University with direct, source-grounded answers to academic inquiries. 

Academic institutional information—such as course syllabi, semester academic calendars, examination schedules, grading regulations, and departmental notices—is often distributed across fragmented PDFs and documents. SRU Assistant bridges this gap with a modern Retrieval-Augmented Generation (RAG) architecture.

> **Core Principle:**
> *"Retrieve first. Generate second. Cite the evidence."*

The Large Language Model (LLM) is not treated as the source of truth for university policies. The university's official documents serve as the authoritative knowledge base, while the LLM synthesizes natural-language answers strictly grounded in retrieved document evidence accompanied by precise citations.

---

## 2. Project Independence

SRU Assistant is an entirely independent capstone engineering project. It is **not** part of the RYU AI Framework and does not inherit or use RYU's architecture, terminology, runtime, agents, workers, spaces, memory systems, or autonomous-agent design.

---

## 3. High-Level Architecture

```text
                    ┌──────────────────────────┐
                    │   SR University Sources  │
                    │ Syllabi, Calendars, etc. │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Document Ingestion     │
                    │ Extraction & Structuring │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Chunking & Embeddings    │
                    │ Vector DB & Lexical Index│
                    └────────────┬─────────────┘
                                 │
 Student Query ────────► Query Processing
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Hybrid Retrieval         │
                    │ Vector + BM25 + Re-rank  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ LLM Grounded Generation  │
                    │ Context + Answer Synth   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Answer + Source Citation │
                    └──────────────────────────┘
```

---

## 4. Current Phase & Status

- **Current Phase:** `Phase 0 — Project Foundation`
- **Current Status:** Repository foundation established.
- **RAG Capability:** Not yet implemented. Text extraction, vector indexing, retrieval, and generation will be implemented sequentially in subsequent roadmap phases.

---

## 5. Specification & Documentation

The project is guided by four foundational specification documents:

1. [`framework.md`](file:///d:/CapProject/framework.md) — Comprehensive framework definition, system layers, requirements, and design principles.
2. [`RAG.md`](file:///d:/CapProject/RAG.md) — Detailed RAG architecture specification covering hybrid search, fusion, re-ranking, and evidence grounding.
3. [`roadmap.md`](file:///d:/CapProject/roadmap.md) — Step-by-step engineering roadmap detailing phases 0 through 14.
4. [`agent.md`](file:///d:/CapProject/agent.md) — Engineering guidelines, phase completion rules, and project memory tracking.

Project engineering records are maintained in [`project_memory/`](file:///d:/CapProject/project_memory/README.md).

---

## 6. Repository Structure

```text
sru-assistant/
│
├── app/                  # Application layer (API, services, config)
│   ├── api/              # API endpoints and schemas
│   ├── services/         # Application service coordinators
│   └── config/           # Application configuration and settings
│
├── ingestion/            # Document ingestion pipeline
│   ├── loaders/          # PDF, DOCX, text file loaders
│   ├── processors/       # Cleaning, normalization, structure detection
│   ├── chunking/         # Academic structure-aware chunking
│   └── metadata/         # Metadata schema and assignment
│
├── retrieval/            # Hybrid retrieval pipeline
│   ├── embeddings/       # Embedding model interfaces
│   ├── vectorstore/      # Vector database integration
│   ├── lexical/          # BM25 / keyword search
│   ├── fusion/           # Hybrid search fusion (e.g. RRF)
│   ├── filtering/        # Metadata-based filtering
│   └── reranking/        # Cross-encoder re-ranking
│
├── generation/           # Answer synthesis layer
│   ├── prompts/          # Grounded prompt templates
│   ├── llm/              # LLM provider clients
│   └── response/         # Response structuring & grounding validation
│
├── citations/            # Provenance and source citation tracking
│
├── evaluation/           # Evaluation metrics and benchmarks
│   ├── datasets/         # Evaluation query sets and ground truth
│   ├── retrieval/        # Retrieval metrics (Recall@K, MRR, NDCG)
│   ├── generation/       # Generation metrics (Faithfulness, Groundedness)
│   └── reports/          # Evaluation reports
│
├── documents/            # Document knowledge base staging
│   ├── raw/              # Unmodified original documents
│   └── processed/        # Extracted text and structured data
│
├── tests/                # Test suite
│   ├── ingestion/        # Ingestion tests
│   ├── retrieval/        # Retrieval tests
│   ├── generation/       # Generation tests
│   ├── citations/        # Citation tests
│   ├── evaluation/       # Evaluation tests
│   └── integration/      # End-to-end integration tests
│
├── frontend/             # User interface (future phases)
├── scripts/              # Developer scripts and batch jobs
├── configs/              # Model and pipeline configuration files
├── project_memory/       # Historical engineering log & phase reports
│
├── .gitignore            # Git ignore configuration
├── .env.example          # Environment variable template
├── pyproject.toml        # Build system & dependency specification
├── requirements.txt      # Base Python dependencies
├── framework.md          # Framework specification
├── RAG.md                # RAG architecture specification
├── roadmap.md            # Project roadmap
└── agent.md              # Engineering agent rules & standards
```

---

## 7. Quick Start (Development Setup)

### Prerequisites

- Python 3.10+ (Tested on Python 3.11)

### Setup Environment

1. Clone or navigate to the repository directory:
   ```bash
   cd sru-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/macOS:
   source .venv/bin/activate
   ```

3. Install foundation dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment variables:
   ```bash
   cp .env.example .env
   ```

5. Run test suite:
   ```bash
   pytest -v
   ```

6. Start Application Server:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```
   - **Student / Faculty Query Portal:** [http://localhost:8000](http://localhost:8000)
   - **Capstone Viva Slide Deck:** [http://localhost:8000/presentation](http://localhost:8000/presentation)
   - **OpenAPI Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 8. Takeover & Verification Documentation
Comprehensive engineering takeover reports and audits are available in `docs/takeover/`:
- `docs/takeover/PROJECT_TAKEOVER_CHECKLIST.md` — Machine-readable verification checklist
- `docs/takeover/FINAL_HANDOVER_REPORT.md` — Executive takeover and completion report
- `docs/takeover/ARCHITECTURE_WALKTHROUGH.md` — Deep dive into RAG architectural layers
- `docs/takeover/FINAL_TEST_RESULTS.md` — Final regression test counts and defect fixes
- `docs/takeover/END_TO_END_DEMO.md` — 13 reproducible step-by-step demo scenarios
- `docs/takeover/BENCHMARK_REPRODUCIBILITY.md` — Empirical evaluation replication
- `docs/takeover/SECURITY_REVIEW.md` — Security and reliability threat modeling

