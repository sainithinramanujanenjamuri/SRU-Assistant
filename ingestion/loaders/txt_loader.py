"""Plain text document loader supporting multiple encodings and line provenance."""
from __future__ import annotations


from pathlib import Path

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


class TXTLoader(BaseDocumentLoader):
    """Loader for plain text (.txt) institutional notices and guidelines."""


    def __init__(self, encoding_fallbacks: list[str] | None = None) -> None:
        self.encoding_fallbacks = encoding_fallbacks or ["utf-8", "utf-8-sig", "latin-1"]

    @property
    def supported_extensions(self) -> list[str]:
        return [".txt"]

    def load(self, path: Path) -> ExtractedDocument:
        """Extract lines and paragraphs from a text file, preserving 1-indexed line numbers."""
        self.validate_file(path)
        doc_id = compute_file_sha256(path)

        content: str | None = None
        used_encoding: str | None = None

        for encoding in self.encoding_fallbacks:
            try:
                content = path.read_text(encoding=encoding)
                used_encoding = encoding
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            raise CorruptedDocumentError(
                f"Failed to decode text file with supported encodings: {self.encoding_fallbacks}",
                file_path=path,
            )

        if not content.strip():
            raise EmptyDocumentError(f"Text document is empty: {path.name}", file_path=path)

        elements: list[DocumentElement] = []
        elem_counter = 0

        lines = content.splitlines()
        for line_idx, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            elem_counter += 1
            line_number = line_idx + 1

            if stripped_line.startswith(("#", "SECTION", "REGULATION", "NOTICE:", "CIRCULAR:")):
                elem_type = ElementType.HEADING
            elif stripped_line.startswith(("- ", "* ", "• ", "1.", "2.", "3.", "4.", "5.")):
                elem_type = ElementType.LIST_ITEM
            else:
                elem_type = ElementType.PARAGRAPH

            elements.append(
                DocumentElement(
                    element_id=f"{doc_id}_elem_{elem_counter:04d}",
                    element_type=elem_type,
                    content=stripped_line,
                    provenance=ElementProvenance(
                        document_id=doc_id,
                        source_file=path.name,
                        page_number=None,
                        line_number=line_number,
                        structural_index=elem_counter,
                    ),
                    metadata={"original_line_number": line_number},
                )
            )

        return ExtractedDocument(
            document_id=doc_id,
            file_path=str(path.resolve()),
            file_name=path.name,
            file_type=".txt",
            file_size_bytes=path.stat().st_size,
            raw_text=content,
            elements=elements,
            loader_name="TXTLoader",
            extraction_metadata={"encoding": used_encoding, "total_lines": len(lines)},
        )
