# SRU Assistant — Frontend User Interface (Student-First Academic Redesign)

This directory contains the redesigned web client for **SRU Assistant — A RAG Framework for University Academic Query Resolution**.

---

## 1. Architectural Overview

The frontend is engineered as a clean, accessible, zero-dependency single-page application (SPA) focused on university students and academic administrators:

1. **Student Experience (Default View)**:
   - Polished welcome canvas with academic starter question cards (Exam Schedules, Attendance Rules, Curriculum & Credits, Regulations).
   - Main conversation area with clear distinction between student inquiries and verified assistant syntheses.
   - Grounding Trust Shield indicating verified institutional evidence.
   - Interactive citation chips (`[1]`, `[2]`) in-text and source cards in an evidence tray.
   - Citation Evidence Drawer Modal presenting document names, page/section provenance, extracted academic claims, and raw retrieved passages.
   - Responsive, keyboard-accessible input composer (`Enter` to submit, `Shift+Enter` for newlines).

2. **System & Administration View**:
   - Telemetry dashboard tracking LLM provider (`ollama` / `qwen3.5:4b`), embedding provider (`fasthash`), vector records count (`22`), and BM25 index synchronization.
   - Interactive retrieval pipeline selector (`Enhanced RAG`, `Hybrid RAG`, `Dense Vector`).
   - Official university document ingestion dropzone supporting `.pdf`, `.docx`, and `.txt` up to 25 MB with SHA-256 duplicate validation.
   - Institutional document catalog table reflecting real-time SQLite/index records.

3. **Removed Legacy Clutter**:
   - The former **Viva Slides** navigation button and associated UI links have been completely removed.
   - Technical monitoring panels have been relocated out of the default student view into the System view.

---

## 2. File Organization

```
frontend/
├── index.html          # Semantic HTML5 application shell & view templates
├── styles.css          # Academic Design System (CSS variables, responsive layouts)
├── app.js              # Client-side controller, API client, markdown parser, modal handlers
└── README.md           # Architecture and technical documentation
```

---

## 3. Protected Backend API Contracts

The frontend interacts with the FastAPI backend without altering any backend routes or contracts:

| Endpoint | Method | Payload / Parameters | Purpose |
| :--- | :---: | :--- | :--- |
| `/api/health` | `GET` | — | Retrieves operational health, model provider, and index status |
| `/api/documents` | `GET` | — | Retrieves list of indexed institutional documents and chunk counts |
| `/api/documents/upload` | `POST` | `multipart/form-data`, `?auto_index=true` | Uploads official documents with size and duplicate hash validation |
| `/api/query` | `POST` | `{ "query": str, "top_k": int, "retrieval_mode": str, "verify_citations": bool }` | Grounded academic resolution with verified citations and telemetry |

---

## 4. Responsive Breakpoints

- **Desktop (>= 1024px):** Persistent 280px sidebar, 840px max-width conversation stream, side-by-side admin panels.
- **Tablet (768px - 1024px):** Compact 250px sidebar, single-column admin panels, responsive cards.
- **Mobile (< 768px):** Collapsible off-canvas drawer with touch backdrop, hamburger menu toggle, single-column starter cards, and full-width touch-friendly composer.
