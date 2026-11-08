"""DOCX document loader using python-docx.

Extracts paragraphs, headings, and structured tables with full grid preservation and provenance.
"""
from __future__ import annotations



from pathlib import Path

import docx
from docx.table import Table
from docx.text.paragraph import Paragraph

from ingestion.loaders.base import (
    BaseDocumentLoader,
    CorruptedDocumentError,
    EmptyDocumentError,
    compute_file_sha256,
)
from ingestion.models import (
    DocumentElement,
    ElementProvenance,
    ElementType,
    ExtractedDocument,
    TableData,
)


class DOCXLoader(BaseDocumentLoader):
    """Loader for Microsoft Word (.docx) documents."""

    @property
    def supported_extensions(self) -> list[str]:
        return [".docx"]

    @staticmethod
    def _format_table_markdown(headers: list[str], rows: list[list[str]]) -> str:
        """Render table grid as GitHub-flavored markdown."""
        if not headers and not rows:
            return ""

        effective_headers = headers if headers else [f"Col {i+1}" for i in range(len(rows[0]))]
        col_count = len(effective_headers)

        lines = [
            "| " + " | ".join(h.replace("\n", " ").strip() for h in effective_headers) + " |",
            "| " + " | ".join(["---"] * col_count) + " |",
        ]

        for row in rows:
            padded_row = (row + [""] * col_count)[:col_count]
            lines.append("| " + " | ".join(c.replace("\n", " ").strip() for c in padded_row) + " |")

        return "\n".join(lines)

    def load(self, path: Path) -> ExtractedDocument:
        """Extract text, headings, and structured tables from a DOCX file."""
        self.validate_file(path)
        doc_id = compute_file_sha256(path)

        try:
            doc = docx.Document(str(path))
        except Exception as e:
            raise CorruptedDocumentError(f"Malformed or corrupted DOCX file: {e}", file_path=path) from e

        elements: list[DocumentElement] = []
        raw_text_parts: list[str] = []
        elem_counter = 0

        # Traverse document elements in exact document flow order
        try:
            body_children = list(doc.element.body)
        except Exception:
            body_children = []

        if body_children:
            for child in body_children:
                tag = child.tag
                if tag.endswith("p"):
                    p = Paragraph(child, doc)
                    text = p.text.strip()
                    if not text:
                        continue

                    elem_counter += 1
                    raw_text_parts.append(text)
                    style_name = p.style.name.lower() if p.style and p.style.name else ""

                    if "title" in style_name:
                        elem_type = ElementType.TITLE
                    elif "heading" in style_name:
                        elem_type = ElementType.HEADING
                    elif "list" in style_name or "bullet" in style_name:
                        elem_type = ElementType.LIST_ITEM
                    else:
                        elem_type = ElementType.PARAGRAPH

                    elements.append(
                        DocumentElement(
                            element_id=f"{doc_id}_elem_{elem_counter:04d}",
                            element_type=elem_type,
                            content=text,
                            provenance=ElementProvenance(
                                document_id=doc_id,
                                source_file=path.name,
                                page_number=None,  # DOCX has no physical pages
                                line_number=None,
                                structural_index=elem_counter,
                            ),
                            metadata={"style": style_name},
                        )
                    )

                elif tag.endswith("tbl"):
                    t = Table(child, doc)
                    raw_grid: list[list[str]] = []
                    for row in t.rows:
                        row_cells = [cell.text.strip() for cell in row.cells]
                        raw_grid.append(row_cells)

                    if not raw_grid or all(not any(c for c in r) for r in raw_grid):
                        continue

                    elem_counter += 1
                    headers = raw_grid[0]
                    data_rows = raw_grid[1:] if len(raw_grid) > 1 else []
                    md_table = self._format_table_markdown(headers, data_rows)

                    raw_text_parts.append(md_table)

                    table_data = TableData(
                        headers=headers,
                        rows=data_rows,
                        num_rows=len(raw_grid),
                        num_cols=len(headers),
                        markdown=md_table,
                    )

                    elements.append(
                        DocumentElement(
                            element_id=f"{doc_id}_elem_{elem_counter:04d}",
                            element_type=ElementType.TABLE,
                            content=md_table,
                            provenance=ElementProvenance(
                                document_id=doc_id,
                                source_file=path.name,
                                page_number=None,
                                line_number=None,
                                structural_index=elem_counter,
                            ),
                            table_data=table_data,
                            metadata={"num_rows": len(raw_grid), "num_cols": len(headers)},
                        )
                    )
        else:
            # Fallback for empty body structure
            for p in doc.paragraphs:
                text = p.text.strip()
                if text:
                    elem_counter += 1
                    raw_text_parts.append(text)
                    elements.append(
                        DocumentElement(
                            element_id=f"{doc_id}_elem_{elem_counter:04d}",
                            element_type=ElementType.PARAGRAPH,
                            content=text,
                            provenance=ElementProvenance(
                                document_id=doc_id,
                                source_file=path.name,
                                structural_index=elem_counter,
                            ),
                        )
                    )

        full_raw_text = "\n\n".join(raw_text_parts)
        if not full_raw_text.strip():
            raise EmptyDocumentError(f"DOCX file contains no text content: {path.name}", file_path=path)

        return ExtractedDocument(
            document_id=doc_id,
            file_path=str(path.resolve()),
            file_name=path.name,
            file_type=".docx",
            file_size_bytes=path.stat().st_size,
            raw_text=full_raw_text,
            elements=elements,
            loader_name="DOCXLoader",
            extraction_metadata={"total_elements": len(elements)},
        )
