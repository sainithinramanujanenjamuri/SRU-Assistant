"""Document cleaning and text normalization processor with conservative header/footer filtering."""

import re
import unicodedata
from collections import Counter

from ingestion.models import (
    DocumentElement,
    ElementType,
    ExtractedDocument,
)

# Protected patterns that must NEVER be removed as header/footer
PROTECTED_PATTERNS = [
    re.compile(r"\b(?:R\s*-\s*\d{2}|R\d{2})\b", re.IGNORECASE),  # Regulations like R23, R20
    re.compile(r"\b\d{2}[A-Z]{2,4}\d{3}[A-Z]?\b", re.IGNORECASE),  # Course codes like 23CSE302T
    re.compile(r"\b(?:20\d{2}\s*[-/–]\s*(?:20)?\d{2})\b"),  # Academic years like 2026-27
    re.compile(r"\b(?:Mid[- ]Semester|End[- ]Semester|Examination|Schedule|Date\s*Sheet)\b", re.IGNORECASE),
    re.compile(r"\b(?:Semester\s+[I|V|X\d]+|[I|V|X\d]+\s+Semester)\b", re.IGNORECASE),
    re.compile(r"\b(?:Credits?|Syllabus|Curriculum|Regulation|Course\s+Title)\b", re.IGNORECASE),
]


class DocumentCleaner:
    """Cleans and normalizes extracted document elements while preserving provenance and academic entities."""

    def __init__(self, header_footer_threshold: float = 0.8) -> None:
        self.header_footer_threshold = header_footer_threshold

    @staticmethod
    def normalize_text(text: str) -> str:
        """Normalize Unicode characters, strip control characters, and clean whitespace."""
        if not text:
            return ""

        # Normalize unicode to NFKC
        normalized = unicodedata.normalize("NFKC", text)

        # Replace unprintable control characters (except standard tabs and newlines) with space
        normalized = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]+", " ", normalized)

        # Replace non-breaking and unusual spaces with standard space
        normalized = normalized.replace("\u00a0", " ").replace("\u200b", "")

        # Normalize multiple horizontal spaces, preserving newlines
        lines = [re.sub(r"[^\S\r\n]+", " ", line).strip() for line in normalized.splitlines()]

        # Filter out consecutive empty lines
        cleaned_lines: list[str] = []
        last_empty = False
        for line in lines:
            if not line:
                if not last_empty:
                    cleaned_lines.append("")
                    last_empty = True
            else:
                cleaned_lines.append(line)
                last_empty = False

        return "\n".join(cleaned_lines).strip()

    @staticmethod
    def is_protected_academic_content(line: str) -> bool:
        """Check if line contains essential academic content that must not be deleted."""
        for pattern in PROTECTED_PATTERNS:
            if pattern.search(line):
                return True
        return False

    def identify_conservative_headers_footers(
        self, elements: list[DocumentElement]
    ) -> set[str]:
        """Identify repeated header/footer lines across pages using conservative validation."""
        page_elements: dict[int, list[DocumentElement]] = {}
        for elem in elements:
            p_num = elem.provenance.page_number
            if p_num is not None:
                page_elements.setdefault(p_num, []).append(elem)

        total_pages = len(page_elements)
        # Only evaluate header/footer across multi-page documents (>= 3 pages)
        if total_pages < 3:
            return set()

        # Check topmost and bottommost lines of each page
        top_lines: list[str] = []
        bottom_lines: list[str] = []

        for elems in page_elements.values():
            if elems:
                top_line = elems[0].content.strip()
                if top_line:
                    top_lines.append(top_line)
            if len(elems) > 1:
                bot_line = elems[-1].content.strip()
                if bot_line:
                    bottom_lines.append(bot_line)

        top_counts = Counter(top_lines)
        bottom_counts = Counter(bottom_lines)

        candidates_to_remove: set[str] = set()

        for line, count in top_counts.items():
            frequency = count / total_pages
            if frequency >= self.header_footer_threshold:
                if not self.is_protected_academic_content(line):
                    candidates_to_remove.add(line)

        for line, count in bottom_counts.items():
            frequency = count / total_pages
            if frequency >= self.header_footer_threshold:
                if not self.is_protected_academic_content(line):
                    candidates_to_remove.add(line)

        return candidates_to_remove

    def clean(self, extracted_doc: ExtractedDocument) -> list[DocumentElement]:
        """Produce a transformed, cleaned list of DocumentElements preserving unbroken provenance.

        Does not modify the original extracted_doc.elements list.
        """
        repeated_headers_footers = self.identify_conservative_headers_footers(extracted_doc.elements)
        cleaned_elements: list[DocumentElement] = []

        for elem in extracted_doc.elements:
            # If element is a table, preserve table structure and markdown
            if elem.element_type == ElementType.TABLE:
                cleaned_elements.append(
                    DocumentElement(
                        element_id=elem.element_id,
                        element_type=ElementType.TABLE,
                        content=elem.content,
                        provenance=elem.provenance.model_copy(),
                        table_data=elem.table_data.model_copy() if elem.table_data else None,
                        metadata=dict(elem.metadata),
                    )
                )
                continue

            normalized_content = self.normalize_text(elem.content)
            if not normalized_content:
                continue

            # Check if this line was identified as a non-academic repetitive header/footer
            if normalized_content in repeated_headers_footers:
                continue

            # Retain element with full unbroken provenance
            cleaned_elements.append(
                DocumentElement(
                    element_id=elem.element_id,
                    element_type=elem.element_type,
                    content=normalized_content,
                    provenance=elem.provenance.model_copy(),
                    table_data=None,
                    metadata=dict(elem.metadata),
                )
            )

        return cleaned_elements
