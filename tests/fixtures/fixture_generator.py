"""Deterministic synthetic fixture generator for SRU Assistant testing.

Creates small, valid PDF, DOCX, and TXT files for test suites.
NOTE: These files are strictly synthetic test fixtures and are distinct from real SR University archives.
"""
from __future__ import annotations



import io
from pathlib import Path

import docx


def build_pdf_bytes(page_lines: list[list[str]]) -> bytes:
    """Generate valid PDF byte stream containing the specified text lines per page."""
    objects: list[bytes] = []
    # 1: Catalog
    objects.append(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    # 2: Pages container
    kid_refs = " ".join(f"{i + 3} 0 R" for i in range(len(page_lines)))
    objects.append(f"2 0 obj\n<< /Type /Pages /Kids [{kid_refs}] /Count {len(page_lines)} >>\nendobj\n".encode("latin1"))

    current_obj_idx = 3 + len(page_lines)
    font_obj_idx = current_obj_idx + len(page_lines)

    page_objs: list[bytes] = []
    content_objs: list[bytes] = []
    for i, lines in enumerate(page_lines):
        page_idx = 3 + i
        content_idx = current_obj_idx + i
        page_obj = f"{page_idx} 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents {content_idx} 0 R /Resources << /Font << /F1 {font_obj_idx} 0 R >> >> >>\nendobj\n".encode("latin1")
        page_objs.append(page_obj)

        stream_parts = ["BT", "/F1 12 Tf", "72 720 Td"]
        for line in lines:
            safe_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
            stream_parts.append(f"({safe_line}) Tj")
            stream_parts.append("0 -18 Td")
        stream_parts.append("ET")
        stream_data = "\n".join(stream_parts).encode("latin1")
        content_obj = f"{content_idx} 0 obj\n<< /Length {len(stream_data)} >>\nstream\n".encode("latin1") + stream_data + b"\nendstream\nendobj\n"
        content_objs.append(content_obj)

    font_obj = f"{font_obj_idx} 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n".encode("latin1")

    all_objs = objects + page_objs + content_objs + [font_obj]

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in all_objs:
        offsets.append(out.tell())
        out.write(obj)

    xref_pos = out.tell()
    out.write(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode("latin1"))
    for off in offsets[1:]:
        out.write(f"{off:010d} 00000 n \n".encode("latin1"))
    out.write(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref_pos}\n%%EOF".encode("latin1"))
    return out.getvalue()


def create_synthetic_pdf(path: Path, pages: list[list[str]]) -> Path:
    """Create a synthetic PDF file with specified pages."""
    path.parent.mkdir(parents=True, exist_ok=True)
    pdf_bytes = build_pdf_bytes(pages)
    path.write_bytes(pdf_bytes)
    return path


def create_synthetic_docx(
    path: Path,
    title: str,
    paragraphs: list[str],
    table_data: tuple[list[str], list[list[str]]] | None = None,
) -> Path:
    """Create a synthetic DOCX file with headings, paragraphs, and optional tables."""
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = docx.Document()
    doc.add_heading(title, level=0)

    for p in paragraphs:
        if p.startswith("Heading:"):
            doc.add_heading(p.replace("Heading:", "").strip(), level=1)
        else:
            doc.add_paragraph(p)

    if table_data:
        headers, rows = table_data
        t = doc.add_table(rows=1 + len(rows), cols=len(headers))
        # Headers
        for col_idx, h in enumerate(headers):
            t.cell(0, col_idx).text = h
        # Data rows
        for row_idx, row in enumerate(rows):
            for col_idx, val in enumerate(row):
                t.cell(row_idx + 1, col_idx).text = val

    doc.save(str(path))
    return path


def create_synthetic_txt(path: Path, content: str) -> Path:
    """Create a synthetic TXT file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path
