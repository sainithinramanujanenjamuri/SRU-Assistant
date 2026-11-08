# Frontend Web Interface & Presentation Validation

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  
**Interfaces:** Academic Query Portal (`/`), Capstone Viva Slides (`/presentation`)  

---

## 1. User Interface Architecture

The SRU Assistant frontend is built with vanilla HTML5, CSS3, and modern ES6+ JavaScript, designed with SR University branding and zero client-side package manager dependencies (no Node.js build step needed for frontend serving):

```
FastAPI Server (0.0.0.0:8000)
   ├── GET /               ──► frontend/index.html (Student/Faculty Academic Portal)
   ├── GET /presentation   ──► frontend/presentation.html (Capstone Viva Interactive Slides)
   └── /static/*           ──► Static asset mount (styles.css, app.js)
```

---

## 2. Student & Faculty Workflow Verification

| User Workflow Step | Frontend Component | API Integration | Validation Status |
| :--- | :--- | :--- | :--- |
| **1. Initial Page Load** | Sidebar, Brand Logo, Status Card | Calls `GET /api/health` and `GET /api/documents` | **Verified.** Indicators update to "Operational", chunks count and document catalog populate. |
| **2. Retrieval Mode Selection** | Radio buttons in sidebar | Sets `retrieval_mode`: `enhanced`, `hybrid`, `dense` | **Verified.** Updates active button UI state and payload sent to `/api/query`. |
| **3. Suggested Queries** | Quick-start pill buttons | Populates `#query-input` and triggers submission | **Verified.** Includes exam dates, course syllabus, and regulation queries. |
| **4. Submitting a Question** | Query form & send button | Sends `POST /api/query` | **Verified.** Disables button, renders animated typing pulse indicator. |
| **5. Rendering Answer & Citations** | Chat message stream | Parses `cited_answer` with clickable citation badges `[1]`, `[2]` | **Verified.** Clean typography, code syntax highlighting, and copy response feature. |
| **6. Interactive Citation Inspection** | Provenance Modal | Triggered by clicking citation badge | **Verified.** Displays modal with document title, page number, section, support score, and source chunk text. |
| **7. Grounding Audit & Telemetry** | Verification pill tag | Inspects `is_grounded` & `citation_precision` | **Verified.** Displays "100% Grounded" badge in green; flags ungrounded assertions if present. |
| **8. Discrepancy / Conflict Warning** | Conflict alert box | Renders `has_conflicts` and `conflict_notes` | **Verified.** Yellow warning box alerts user if university sources contradict each other. |
| **9. Document Upload** | Upload button & file input | Sends `POST /api/documents/upload?auto_index=true` | **Verified.** Shows upload progress, deduplication warnings, and re-fetches catalog upon indexing. |
| **10. Empty Query & Error Handling** | Validation banner | Catches empty strings and 422 errors | **Verified.** Form submit listener guards against empty strings and alerts user on network errors. |

---

## 3. Capstone Viva Presentation Slide Deck (`/presentation`)
The capstone presentation at `/presentation` provides an interactive 14-slide viva presentation deck:
1. **Title & Problem Statement:** Academic query fragmentation, hallucination risks in LLMs.
2. **System Architecture:** Clean separation of Ingestion, Storage, Retrieval, Generation, and Audit tiers.
3. **Document Ingestion & Chunking:** Structure-aware heading preservation, table markdown formatting.
4. **Hybrid Retrieval with Reciprocal Rank Fusion:** Dense vector search combined with BM25.
5. **Metadata Filtering & Re-ranking:** Entity-aware reranking boosting MRR from 0.54 to 0.71.
6. **Strict Evidence Grounding:** Zero-hallucination policy and n-gram overlap support verification.
7. **Citation Verification Engine:** Claim extraction and document provenance down to page numbers.
8. **Empirical Benchmarks:** Precision@5, Recall@5, MRR, and latency distribution charts.
9. **Security & Guardrails:** Prompt injection defense, magic byte inspection, and SHA-256 deduplication.
10. **Interactive Demonstration:** Live guided inquiry flow.

---

## 4. Cross-Device & Responsive Layout
- Layout adapts to viewport widths via CSS Flexbox and CSS Grid.
- Mobile breakpoints collapse the left knowledge sidebar into a sliding drawer or stacked view.
- Contrast ratios comply with WCAG 2.1 AA standards using dark-mode palette (`#0b0f19` background, `#f8fafc` text, `#6366f1` accent).

