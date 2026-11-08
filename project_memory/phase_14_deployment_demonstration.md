# Phase 14 — Deployment & Demonstration: Capstone Viva-Voce Completion

## 1. Objective

Deliver all final capstone presentation materials, academic thesis documentation, live demonstration scenarios, and defense guides required for the final evaluation of **SRU Assistant: A RAG Framework for University Academic Query Resolution** by **Capstone Project Team No. 235**, School of Computer Science & Artificial Intelligence, SR University.

---

## 2. Deliverables Summary

### 2.1 Live Application Deployment
- **Local Daemon:** FastAPI / Uvicorn server active on `http://127.0.0.1:8000`.
- **API Documentation:** Interactive Swagger OpenAPI 3.0 at `http://127.0.0.1:8000/docs`.
- **Student User Interface:** Responsive glassmorphic web application at `http://127.0.0.1:8000/`.
- **Navigation Integration:** Top navigation header links directly to the **Viva Slides** deck and the **API Docs**.

### 2.2 Presentation Materials (15 Slides)
- **Interactive Web Slide Deck:** [frontend/presentation.html](file:///Users/saisunkari/Desktop/4TH%20YEAR/CAPSTONE%20PROJECT/frontend/presentation.html)
  - Accessible via `http://127.0.0.1:8000/presentation.html` or `http://127.0.0.1:8000/presentation`.
  - Features: Slide-by-slide transitions, progress indicator, speaker notes panel (toggled with `N`), full-screen presentation mode (`F`), and print/PDF formatting (`P`).
  - Covers: Title (Team 235), Problem Statement, System Architecture, Chunking Strategy, Dual Dense-Sparse Indexing, Reciprocal Rank Fusion ($k=60$), Two-Stage Re-ranking, Grounded Generation & Safe Refusal, Citation Provenance, Security Guardrails, Phase 9 Ablation Results (+25.9% MRR gain), Live Demos, Engineering Rigor (309 tests), and Future Scope.
- **Markdown Slide Deck:** [docs/presentation/capstone_viva_slides.md](file:///Users/saisunkari/Desktop/4TH%20YEAR/CAPSTONE%20PROJECT/docs/presentation/capstone_viva_slides.md)
  - Ready for export into PowerPoint, Google Slides, or Marp.

### 2.3 Capstone Project Book / Thesis Report
- **Document Path:** [docs/SRU_Assistant_Capstone_Project_Report.md](file:///Users/saisunkari/Desktop/4TH%20YEAR/CAPSTONE%20PROJECT/docs/SRU_Assistant_Capstone_Project_Report.md)
- **Formatting Standards:** Conforms to SR University B.Tech capstone thesis guidelines.
- **Included Sections:**
  - Institutional Title Page (School of CS&AI, Team 235, Guide, Semester VII).
  - Official Certificate of Bonafide Work.
  - Declaration of Originality.
  - Acknowledgments & Abstract.
  - Chapter 1: Introduction (Background, Problem Statement, Objectives, Scope).
  - Chapter 2: Literature Review (Classical IR vs Dense DPR, RRF, RAG Hallucination Mitigation).
  - Chapter 3: System Architecture (Ingestion, Chunking, Dual Indexing, RRF, Re-ranking, Provenance, Security).
  - Chapter 4: Implementation & Algorithms (Recursive Chunker, RRF formulation, Safe Refusal, Citation Verification, REST API).
  - Chapter 5: Experimental Evaluation & Results (Phase 9 Benchmark, Experiments A, B, C, D ablations, Category analysis, Latency breakdown).
  - Chapter 6: Conclusion & Future Scope (Local Small LLMs via Ollama, Vernacular Telugu/Hindi, ERP integration).
  - References: IEEE format bibliography.

### 2.4 Viva Demonstration & Defense Guide
- **Document Path:** [capstone_viva_demonstration_guide.md](file:///Users/saisunkari/.gemini/antigravity-ide/brain/7d18eb96-512d-4991-bd38-239adb6117bd/capstone_viva_demonstration_guide.md)
- Contains step-by-step oral scripts for 5 live demonstration scenarios and defense answers for 10 challenging viva-voce questions from external examiners.

---

## 3. Empirical Verification & Evidence

### 3.1 Test Suite Status
```bash
.venv/bin/pytest tests/
```
**Output:**
```
============================= 309 passed in 1.05s ==============================
```

### 3.2 Live End-to-End Route Validation
- `GET /api/health` $\rightarrow$ `200 OK`
- `GET /` $\rightarrow$ `200 OK` (Serves `frontend/index.html`)
- `GET /presentation` $\rightarrow$ `200 OK` (Serves `frontend/presentation.html`)
- `POST /api/query` $\rightarrow$ `200 OK` with grounded answer and citation metadata.

---

## 4. Milestone Gate Status

- **Code:** Complete and integrated across all modules.
- **Tests:** 100% passing (309/309).
- **Presentation Deck:** Available in interactive HTML and Markdown.
- **Project Report:** Complete academic book available in `docs/`.
- **Status:** **COMPLETED**
