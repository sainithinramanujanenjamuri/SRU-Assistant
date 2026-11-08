"""Evidence-based metadata extraction without metadata fabrication."""
from __future__ import annotations



import re
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc


from ingestion.models import (
    DetectedAcademicStructures,
    DocumentMetadata,
    ExtractedDocument,
)

PROGRAM_PATTERNS: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bB\.?\s*Tech(?:\.?|\b)", re.IGNORECASE), "B.Tech"),
    (re.compile(r"\bM\.?\s*Tech(?:\.?|\b)", re.IGNORECASE), "M.Tech"),
    (re.compile(r"\bPh\.?\s*D(?:\.?|\b)", re.IGNORECASE), "Ph.D."),
    (re.compile(r"\bMBA\b", re.IGNORECASE), "MBA"),
    (re.compile(r"\bBBA\b", re.IGNORECASE), "BBA"),
    (re.compile(r"\bB\.?\s*Pharm(?:\.?|\b)", re.IGNORECASE), "B.Pharm"),
]


class MetadataExtractor:
    """Extracts verified metadata from extracted documents and detected academic structures.

    Strictly adheres to the Non-Fabrication principle: if a field is not explicitly supported
    by text evidence, it remains None.
    """

    @staticmethod
    def detect_program(text: str) -> str | None:
        """Detect academic program (B.Tech, M.Tech, etc.) from text evidence only."""
        for pattern, prog in PROGRAM_PATTERNS:
            if pattern.search(text):
                return prog
        return None

    def extract_metadata(
        self,
        extracted_doc: ExtractedDocument,
        structures: DetectedAcademicStructures,
    ) -> DocumentMetadata:
        """Create DocumentMetadata populated exclusively with verified evidence."""
        # Canonical document_id is the full-file SHA-256
        doc_id = extracted_doc.document_id

        # Department: only if exactly one department detected; if ambiguous or multiple, use first or None
        department = structures.departments[0] if len(structures.departments) == 1 else (
            ", ".join(structures.departments) if structures.departments else None
        )

        # Academic Year: only if detected
        academic_year = structures.academic_years[0] if structures.academic_years else None

        # Semester: only if detected
        semester = structures.semesters[0] if structures.semesters else None

        # Category: only if detected
        category = structures.categories[0] if structures.categories else None

        # Program: detect from text evidence
        program = self.detect_program(extracted_doc.raw_text)

        now_iso = datetime.now(UTC).isoformat()

        return DocumentMetadata(
            document_id=doc_id,
            document_name=extracted_doc.file_name,
            source_path=extracted_doc.file_path,
            document_type=extracted_doc.file_type,
            file_size_bytes=extracted_doc.file_size_bytes,
            department=department,
            program=program,
            academic_year=academic_year,
            semester=semester,
            regulations=structures.regulations,
            category=category,
            version=None,
            ingestion_timestamp=now_iso,
        )
