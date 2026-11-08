"""PDF document loader using pypdf.

Extracts page-by-page content preserving 1-indexed page provenance and raw text.
"""

from pathlib import Path

import pypdf
from pypdf.errors import PdfReadError

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
)


class PDFLoader(BaseDocumentLoader):
    """Loader for PDF documents."""

    @property
    def supported_extensions(self) -> list[str]:
        return [".pdf"]

    def load(self, path: Path) -> ExtractedDocument:
        """Extract text and elements from a PDF file."""
        self.validate_file(path)
        doc_id = compute_file_sha256(path)

        try:
            reader = pypdf.PdfReader(str(path))
        except PdfReadError as e:
            raise CorruptedDocumentError(f"Malformed or corrupted PDF: {e}", file_path=path) from e
        except Exception as e:
            raise CorruptedDocumentError(f"Failed to read PDF file: {e}", file_path=path) from e

        if reader.is_encrypted:
            try:
                # Attempt decrypt with empty password for default permissions
                decrypt_success = reader.decrypt("")
                if decrypt_success == 0:
                    raise CorruptedDocumentError("Encrypted PDF with non-empty password cannot be read", file_path=path)
            except Exception as e:
                raise CorruptedDocumentError(f"Unable to decrypt PDF: {e}", file_path=path) from e

        num_pages = len(reader.pages)
        if num_pages == 0:
            raise EmptyDocumentError(f"PDF contains no pages: {path.name}", file_path=path)

        elements: list[DocumentElement] = []
        raw_text_parts: list[str] = []
        elem_counter = 0

        for page_idx, page in enumerate(reader.pages):
            page_number = page_idx + 1
            try:
                page_text = page.extract_text() or ""
            except Exception as e:
                raise CorruptedDocumentError(f"Error extracting text from page {page_number}: {e}", file_path=path) from e

            raw_text_parts.append(page_text)

            # Segment page text into paragraphs/lines
            lines = [line.strip() for line in page_text.splitlines() if line.strip()]
            for line in lines:
                elem_counter += 1
                elem_type = ElementType.PARAGRAPH
                # Heuristic for title/heading on individual lines
                if len(line) < 120 and (line.isupper() or line.startswith(("#", "SECTION", "REGULATION", "COURSE", "UNIT"))):
                    elem_type = ElementType.HEADING

                element = DocumentElement(
                    element_id=f"{doc_id}_elem_{elem_counter:04d}",
                    element_type=elem_type,
                    content=line,
                    provenance=ElementProvenance(
                        document_id=doc_id,
                        source_file=path.name,
                        page_number=page_number,
                        line_number=None,
                        structural_index=elem_counter,
                    ),
                    metadata={"page_number": page_number},
                )
                elements.append(element)

        full_raw_text = "\n\n".join(raw_text_parts)
        if not full_raw_text.strip():
            raise EmptyDocumentError(f"PDF contains no readable text (scanned image or empty): {path.name}", file_path=path)

        return ExtractedDocument(
            document_id=doc_id,
            file_path=str(path.resolve()),
            file_name=path.name,
            file_type=".pdf",
            file_size_bytes=path.stat().st_size,
            raw_text=full_raw_text,
            elements=elements,
            loader_name="PDFLoader",
            extraction_metadata={"total_pages": num_pages},
        )
