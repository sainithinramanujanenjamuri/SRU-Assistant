"""Generate high-quality, comprehensive PDF audit report for SRU Assistant Document Upload & Indexing."""
from __future__ import annotations

import os
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and print total page count and running header/footer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count: int):
        self.saveState()
        self.setFont("Helvetica-Bold", 8)
        self.setFillColor(colors.HexColor("#475569"))

        # Running Header (pages 2+)
        if self._pageNumber > 1:
            self.drawString(
                54,
                750,
                "SRU ASSISTANT — OFFICIAL DOCUMENT UPLOAD & INDEXING AUDIT REPORT",
            )
            self.setFont("Helvetica", 8)
            self.drawRightString(612 - 54, 750, "TECHNICAL ARCHITECTURE & SECURITY AUDIT")
            self.setStrokeColor(colors.HexColor("#CBD5E1"))
            self.setLineWidth(0.5)
            self.line(54, 744, 612 - 54, 744)

        # Running Footer (all pages)
        self.setStrokeColor(colors.HexColor("#CBD5E1"))
        self.setLineWidth(0.5)
        self.line(54, 45, 612 - 54, 45)

        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))
        self.drawString(
            54,
            33,
            "SR University Capstone Project • AI Systems Architecture & Security Group",
        )
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 33, page_str)
        self.restoreState()


def build_audit_pdf(output_path: str):
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom typography styles
    title_style = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=14,
        spaceAfter=6,
        keepWithNext=True,
    )

    h2_style = ParagraphStyle(
        "Heading2_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#334155"),
        spaceBefore=10,
        spaceAfter=4,
        keepWithNext=True,
    )

    body_style = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#334155"),
        spaceAfter=6,
    )

    bullet_style = ParagraphStyle(
        "Bullet_Custom",
        parent=body_style,
        leftIndent=14,
        bulletIndent=6,
        spaceAfter=3,
    )

    callout_style = ParagraphStyle(
        "Callout_Custom",
        parent=body_style,
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=12,
        textColor=colors.HexColor("#1E293B"),
    )

    code_style = ParagraphStyle(
        "Code_Custom",
        parent=styles["Normal"],
        fontName="Courier",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10,
        textColor=colors.HexColor("#1E293B"),
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=table_cell_style,
        fontName="Helvetica-Bold",
    )

    story = []

    # Title Block
    story.append(Paragraph("SRU ASSISTANT — TECHNICAL AUDIT REPORT", title_style))
    story.append(
        Paragraph(
            "Comprehensive Audit of Official Document Upload, Parsing, Chunking, Dual-Store Indexing, and Security",
            subtitle_style,
        )
    )
    story.append(
        HRFlowable(
            width="100%",
            thickness=1.5,
            color=colors.HexColor("#2563EB"),
            spaceBefore=0,
            spaceAfter=10,
        )
    )

    # Metadata Card
    meta_data = [
        [
            Paragraph("<b>System:</b> SRU Assistant RAG Platform", table_cell_style),
            Paragraph("<b>Target Model:</b> Qwen3.5:4B (Ollama)", table_cell_style),
        ],
        [
            Paragraph("<b>Subsystem:</b> Document Ingestion & Indexing", table_cell_style),
            Paragraph("<b>Embedding Model:</b> FastHash-384 (384-dim)", table_cell_style),
        ],
        [
            Paragraph("<b>Audit Date:</b> November 2026", table_cell_style),
            Paragraph("<b>Dual Stores:</b> SQLite Vector DB + BM25 JSON", table_cell_style),
        ],
        [
            Paragraph("<b>Role:</b> Senior AI Systems Architect & QA Lead", table_cell_style),
            Paragraph("<b>Status:</b> Read-Only Verified Audit", table_cell_style),
        ],
    ]
    meta_table = Table(meta_data, colWidths=[250, 254])
    meta_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F8FAFC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta_table)
    story.append(Spacer(1, 10))

    # SECTION 1: EXECUTIVE SUMMARY
    story.append(Paragraph("1. Executive Summary", h1_style))
    story.append(
        Paragraph(
            "This technical audit evaluates the official document upload and indexing capabilities of the "
            "SRU Assistant university query resolution framework. The system implements a robust, modular pipeline "
            "converting academic notices, syllabi, calendars, and regulations into synchronized dense vectors and "
            "sparse BM25 inverted index postings. The subsystem guarantees unbroken provenance and strict non-fabrication.",
            body_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Key Strengths:</b> Bounded asynchronous streaming upload (64 KB chunks up to 25 MB) preventing memory DoS; "
            "magic-byte validation for PDF and DOCX; path traversal neutralization; structure-aware chunking preserving heading "
            "hierarchies and table grids; conservative header/footer filtering protecting academic identifiers (e.g., R23); "
            "and multi-stage transactional rollback on partial ingestion failures.",
            bullet_style,
        )
    )
    story.append(
        Paragraph(
            "<b>Key Weaknesses:</b> Synchronous ingestion execution in the HTTP event loop; catalog endpoint scanning filesystem "
            "JSONs rather than SQL vector records; absence of document deletion or re-indexing APIs; lack of OCR for scanned PDFs; "
            "and zero authentication on the upload endpoint.",
            bullet_style,
        )
    )
    story.append(Spacer(1, 6))

    # SECTION 2: ARCHITECTURE & COMPONENT RESPONSIBILITIES
    story.append(Paragraph("2. Project Architecture & Component Responsibilities", h1_style))
    arch_data = [
        [Paragraph("Module / Component", table_header_style), Paragraph("Source File", table_header_style), Paragraph("Key Responsibility", table_header_style)],
        [Paragraph("Upload Route", table_cell_bold), Paragraph("app/api/routes.py", code_style), Paragraph("Handles multipart upload, bounded 64KB streaming read, auto-index coordination.", table_cell_style)],
        [Paragraph("Document Guard", table_cell_bold), Paragraph("app/security/document_guard.py", code_style), Paragraph("Enforces magic-byte check, path traversal sanitization, SHA-256 duplicate registry.", table_cell_style)],
        [Paragraph("Query Service", table_cell_bold), Paragraph("app/services/query_service.py", code_style), Paragraph("Singleton service orchestrating ingestion, transactional rollbacks, and catalog.", table_cell_style)],
        [Paragraph("Document Loaders", table_cell_bold), Paragraph("ingestion/loaders/", code_style), Paragraph("Extracts raw text: pypdf for PDF, python-docx for DOCX (tables), TXT multi-encoding.", table_cell_style)],
        [Paragraph("Document Cleaner", table_cell_bold), Paragraph("ingestion/processors/cleaner.py", code_style), Paragraph("NFKC normalization, whitespace cleanup, header/footer filter protecting academic codes.", table_cell_style)],
        [Paragraph("Structure Detectors", table_cell_bold), Paragraph("ingestion/processors/detectors/", code_style), Paragraph("Modular regex detection for course codes, regulations, semesters, dates, exams.", table_cell_style)],
        [Paragraph("Metadata Extractor", table_cell_bold), Paragraph("ingestion/metadata/extractor.py", code_style), Paragraph("Evidence-based non-fabricating metadata mapping (unsupported fields remain None).", table_cell_style)],
        [Paragraph("Structure Chunker", table_cell_bold), Paragraph("ingestion/chunking/structure_aware.py", code_style), Paragraph("Hierarchical chunking respecting headings, table grids, lists, sentences.", table_cell_style)],
        [Paragraph("Vector Store & Indexer", table_cell_bold), Paragraph("retrieval/vectorstore/", code_style), Paragraph("SQLite vector database (vector_records table), float32 BLOB vectors, cosine search.", table_cell_style)],
        [Paragraph("BM25 Inverted Index", table_cell_bold), Paragraph("retrieval/lexical/", code_style), Paragraph("BM25Okapi inverted index, Robertson IDF, incremental updates with prune_missing=False.", table_cell_style)],
    ]
    arch_table = Table(arch_data, colWidths=[100, 150, 254])
    arch_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(arch_table)
    story.append(Spacer(1, 8))

    # SECTION 3: END-TO-END UPLOAD WORKFLOW
    story.append(Paragraph("3. End-to-End Upload & Indexing Workflow (11 Stages)", h1_style))
    stages = [
        "<b>Stage 1 (Frontend):</b> User clicks upload button in sidebar; client sends multipart/form-data to POST /api/documents/upload?auto_index=true.",
        "<b>Stage 2 (Streaming Intake):</b> API reads 64 KB async chunks; aborts with HTTP 400 if file exceeds 25 MB max limit.",
        "<b>Stage 3 (Security Inspection):</b> DocumentGuard sanitizes filename against path traversal; verifies %PDF- or PK\\x03\\x04 magic headers; checks SHA-256 duplicate registry.",
        "<b>Stage 4 (Raw Storage):</b> Binary written to documents/raw/{safe_filename}.",
        "<b>Stage 5 (Extraction):</b> Resolved loader (PDF/DOCX/TXT) extracts raw text, preserving 1-indexed pages or line provenance.",
        "<b>Stage 6 (Cleaning):</b> DocumentCleaner executes NFKC normalization and suppresses headers/footers while protecting R23, course codes, and exam dates.",
        "<b>Stage 7 (Structure Detection):</b> Modular regex detectors extract course codes, regulations, semesters, dates, and examinations.",
        "<b>Stage 8 (Metadata):</b> MetadataExtractor enforces non-fabrication; writes intermediate document to documents/processed/{doc_id}.json.",
        "<b>Stage 9 (Chunking):</b> StructureAwareChunker preserves section breadcrumbs and tables; tokenized via RegexTokenizer (target: 500, max: 1200).",
        "<b>Stage 10 (Dual Indexing):</b> VectorIndexer embeds chunks into SQLite vector_records; BM25Indexer updates inverted index postings and saves bm25_index.json.",
        "<b>Stage 11 (Transactional Rollback):</b> If any stage fails, rollback guard purges SQLite records, removes BM25 chunks, unlinks JSONs, and deletes the raw file.",
    ]
    for s in stages:
        story.append(Paragraph(s, bullet_style))
    story.append(Spacer(1, 8))

    # SECTION 4: DOCUMENT MANAGEMENT & LIFECYCLE
    story.append(Paragraph("4. Document Management & Lifecycle Matrix", h1_style))
    mgmt_data = [
        [Paragraph("Operation", table_header_style), Paragraph("Status", table_header_style), Paragraph("Implementation Details", table_header_style), Paragraph("Architectural Limitations", table_header_style)],
        [Paragraph("List Catalog", table_cell_bold), Paragraph("Fully Implemented", table_cell_style), Paragraph("GET /api/documents via query_service.get_documents()", table_cell_style), Paragraph("Scans documents/chunks/*.json instead of SQLite records.", table_cell_style)],
        [Paragraph("View Metadata", table_cell_bold), Paragraph("Partially Implemented", table_cell_style), Paragraph("DocumentSummary schema returns name, type, category, chunk count.", table_cell_style), Paragraph("Detailed metadata (regulations, dates, departments) omitted.", table_cell_style)],
        [Paragraph("Delete Document", table_cell_bold), Paragraph("Not Implemented", table_cell_style), Paragraph("Backend stores have delete methods, but NO API route exists.", table_cell_style), Paragraph("Manual file deletion causes desynchronization.", table_cell_style)],
        [Paragraph("Re-index Document", table_cell_bold), Paragraph("Partially Implemented", table_cell_style), Paragraph("CLI scripts available (scripts/build_vector_index.py).", table_cell_style), Paragraph("No programmatic API endpoint for on-demand re-indexing.", table_cell_style)],
        [Paragraph("Deduplication", table_cell_bold), Paragraph("Partially Implemented", table_cell_style), Paragraph("DocumentGuard computes SHA-256 hash and rejects duplicates.", table_cell_style), Paragraph("Known hash set is in-memory only; resets on server restart.", table_cell_style)],
        [Paragraph("Versioning", table_cell_bold), Paragraph("Not Implemented", table_cell_style), Paragraph("Schema declares version field, but always returns None.", table_cell_style), Paragraph("Conflicting documents trigger warnings rather than superseding.", table_cell_style)],
    ]
    mgmt_table = Table(mgmt_data, colWidths=[80, 85, 175, 164])
    mgmt_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(mgmt_table)
    story.append(Spacer(1, 8))

    # SECTION 5: ACADEMIC DOCUMENT INTELLIGENCE
    story.append(Paragraph("5. Academic Document Intelligence Assessment", h1_style))
    story.append(
        Paragraph(
            "<b>Course Plans & Syllabi:</b> DOCX extraction retains course outcomes, lecture breakdown grids, and evaluation "
            "components as Markdown tables. However, PDF extraction flattens table cells into lines, causing table alignment loss.<br/>"
            "<b>Academic Regulations:</b> Identifies regulations (R23, R20), attendance thresholds (75%), condonation ranges (65%–74.9%), "
            "and detention clauses with section-level breadcrumb provenance.<br/>"
            "<b>Academic Calendars:</b> Extracts date spans and exam milestones; cross-document conflict detector actively surfaces "
            "discrepancies between conflicting calendar versions.<br/>"
            "<b>Department Notices:</b> Accurately detects departments (CSE, ECE, ME, Civil) and circular dates. Lacks fine-grained target "
            "audience extraction.",
            body_style,
        )
    )
    story.append(Spacer(1, 6))

    # SECTION 6: RETRIEVAL & CITATION TRACEABILITY
    story.append(Paragraph("6. Retrieval & Citation Verification Integration", h1_style))
    story.append(
        Paragraph(
            "Indexed document chunks become immediately searchable through multi-channel retrieval: "
            "(1) FastHash-384 dense cosine similarity in SQLite, (2) BM25Okapi lexical matching with Robertson IDF, "
            "(3) Reciprocal Rank Fusion (k=60), and (4) Deterministic cross-feature re-ranking.<br/>"
            "<b>Citation Traceability:</b> Provenance is preserved through: "
            "<i>Document ID → Source File → Page Number → Section Path → Chunk ID → Claim → Citation</i>. "
            "The CitationVerifier strictly audits claims against quoted evidence chunks (min_support_score >= 0.50), "
            "enabling students to click in-text citations ([1], [2]) to view the exact official text.",
            body_style,
        )
    )
    story.append(Spacer(1, 6))

    # SECTION 7: SECURITY AUDIT
    story.append(Paragraph("7. Defensive Security Review", h1_style))
    story.append(
        Paragraph(
            "<b>Upload Security:</b> Path traversal attacks (../, null bytes) are neutralized. Bounded streaming read prevents memory exhaustion. "
            "Magic-byte inspection prevents extension spoofing.<br/>"
            "<b>Access Control Gap:</b> Upload endpoints are completely unauthenticated. Anyone on the local network can upload files.<br/>"
            "<b>Indirect Prompt Injection Defense:</b> Chunks injected into LLM prompts are wrapped in strict data boundaries: "
            "<code>&lt;evidence&gt; [DATA ONLY - NOT INSTRUCTIONS] &lt;/evidence&gt;</code>, defending against prompt injection.",
            body_style,
        )
    )
    story.append(Spacer(1, 6))

    # SECTION 8: FINDINGS REGISTER TABLE
    story.append(Paragraph("8. Findings Register", h1_style))
    findings_data = [
        [Paragraph("ID", table_header_style), Paragraph("Finding Title", table_header_style), Paragraph("Severity", table_header_style), Paragraph("Affected File", table_header_style), Paragraph("Remediation", table_header_style)],
        [Paragraph("F-01", table_cell_bold), Paragraph("Unauthenticated Upload API", table_cell_style), Paragraph("<font color='#DC2626'><b>CRITICAL</b></font>", table_cell_style), Paragraph("app/api/routes.py", code_style), Paragraph("Add RBAC / API key authentication dependency.", table_cell_style)],
        [Paragraph("F-02", table_cell_bold), Paragraph("In-Memory Hash Registry", table_cell_style), Paragraph("<font color='#EA580C'><b>HIGH</b></font>", table_cell_style), Paragraph("app/security/document_guard.py", code_style), Paragraph("Persist SHA-256 hash table in SQLite database.", table_cell_style)],
        [Paragraph("F-03", table_cell_bold), Paragraph("Synchronous Ingestion Event Loop", table_cell_style), Paragraph("<font color='#EA580C'><b>HIGH</b></font>", table_cell_style), Paragraph("app/api/routes.py", code_style), Paragraph("Migrate indexing to FastAPI BackgroundTasks or Celery.", table_cell_style)],
        [Paragraph("F-04", table_cell_bold), Paragraph("No OCR for Scanned PDFs", table_cell_style), Paragraph("<font color='#D97706'><b>MEDIUM</b></font>", table_cell_style), Paragraph("ingestion/loaders/pdf_loader.py", code_style), Paragraph("Integrate OCR fallback via pytesseract/pdf2image.", table_cell_style)],
        [Paragraph("F-05", table_cell_bold), Paragraph("Filesystem-Coupled Catalog", table_cell_style), Paragraph("<font color='#D97706'><b>MEDIUM</b></font>", table_cell_style), Paragraph("app/services/query_service.py", code_style), Paragraph("Query vector_records SQLite table for catalog summary.", table_cell_style)],
        [Paragraph("F-06", table_cell_bold), Paragraph("Missing Deletion Endpoint", table_cell_style), Paragraph("<font color='#D97706'><b>MEDIUM</b></font>", table_cell_style), Paragraph("app/api/routes.py", code_style), Paragraph("Expose DELETE /api/documents/{doc_id} with store purge.", table_cell_style)],
        [Paragraph("F-07", table_cell_bold), Paragraph("PDF Table Grid Flattening", table_cell_style), Paragraph("<font color='#D97706'><b>MEDIUM</b></font>", table_cell_style), Paragraph("ingestion/loaders/pdf_loader.py", code_style), Paragraph("Add pdfplumber table extraction matching DOCX quality.", table_cell_style)],
        [Paragraph("F-08", table_cell_bold), Paragraph("Regex Tokenizer Divergence", table_cell_style), Paragraph("<font color='#2563EB'><b>LOW</b></font>", table_cell_style), Paragraph("ingestion/chunking/tokenizer.py", code_style), Paragraph("Option to bind HuggingFace/Tiktoken subword tokenizer.", table_cell_style)],
        [Paragraph("F-09", table_cell_bold), Paragraph("Missing Upload Progress Bar", table_cell_style), Paragraph("<font color='#2563EB'><b>LOW</b></font>", table_cell_style), Paragraph("frontend/app.js", code_style), Paragraph("Add XMLHttpRequest onprogress byte tracking in UI.", table_cell_style)],
    ]
    findings_table = Table(findings_data, colWidths=[35, 115, 65, 135, 154])
    findings_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
            ]
        )
    )
    story.append(findings_table)
    story.append(Spacer(1, 8))

    # SECTION 9: IMPROVEMENT ROADMAP
    story.append(Paragraph("9. Recommended Improvement Roadmap", h1_style))
    roadmap = [
        "<b>Priority 0 (Immediate Security):</b> Implement API token authentication on /api/documents/upload and persist the SHA-256 duplicate hash registry in SQLite.",
        "<b>Priority 1 (Core Reliability):</b> Migrate ingestion to asynchronous BackgroundTasks and implement complete document deletion (DELETE /api/documents/{id}).",
        "<b>Priority 2 (Intelligence):</b> Integrate OCR for scanned PDF notices and pdfplumber structured table grid extraction.",
        "<b>Priority 3 (Retrieval Quality):</b> Implement document version lineage (superseding outdated calendars) and align regex tokenization with active LLMs.",
        "<b>Priority 4 (UX & Observability):</b> Add upload percentage progress bars and an administrative document management modal.",
    ]
    for r in roadmap:
        story.append(Paragraph(r, bullet_style))
    story.append(Spacer(1, 8))

    # SECTION 10: FINAL VERDICT
    story.append(Paragraph("10. Final Audit Verdict", h1_style))
    verdicts = [
        "<b>1. Is upload fully functional?</b> Yes, for valid text, Word, and text-based PDFs. Management operations are missing.",
        "<b>2. Does upload guarantee indexing?</b> Yes, with auto_index=True; failures trigger complete transactional rollback.",
        "<b>3. Are dual stores synchronized?</b> Yes, VectorIndexer and BM25Indexer update synchronously without data divergence.",
        "<b>4. Can it process PDF course plans?</b> Partially; text is extracted safely, but complex table grids are flattened.",
        "<b>5. Does it preserve structure?</b> Yes; headings, section breadcrumbs, table grids (DOCX), and academic codes are preserved.",
        "<b>6. Can students retrieve lecture/unit plans?</b> Accurately for DOCX tables; partially degraded for PDF line streams.",
        "<b>7. Are citations traceable?</b> Yes; 1-indexed pages and line numbers propagate through to student citation modals.",
        "<b>8. Is deletion safe?</b> No, because document deletion is not yet exposed via the API.",
        "<b>9. Is it secure for official university use?</b> No; authentication and access control are missing on the upload endpoint.",
        "<b>10. Top 5 Improvements:</b> (1) Upload RBAC Auth, (2) Document Deletion API, (3) Async Ingestion Queue, (4) Persistent Hash Registry, (5) OCR & PDF Table Extraction.",
    ]
    for v in verdicts:
        story.append(Paragraph(v, bullet_style))

    doc.build(story, canvasmaker=NumberedCanvas)
    return output_path


if __name__ == "__main__":
    out_dir = Path("docs")
    out_dir.mkdir(parents=True, exist_ok=True)
    target_file = out_dir / "SRU_Assistant_Document_Upload_and_Indexing_Audit_Report.pdf"
    print(f"Generating audit PDF at: {target_file.resolve()}")
    build_audit_pdf(str(target_file))
    print(f"Successfully generated PDF: {target_file.stat().st_size} bytes")

