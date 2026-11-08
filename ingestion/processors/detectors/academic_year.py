"""Modular detector for academic years (e.g. 2026-27, 2025-2026)."""

import re

from ingestion.models import DocumentElement
from ingestion.processors.detectors.base import BaseStructureDetector

ACADEMIC_YEAR_PATTERN = re.compile(
    r"\b(20\d{2})\s*[-/–]\s*(20\d{2}|\d{2})\b"
)


class AcademicYearDetector(BaseStructureDetector):
    """Detects academic year periods from text."""

    @property
    def name(self) -> str:
        return "academic_year_detector"

    def detect(self, elements: list[DocumentElement], full_text: str) -> list[str]:
        """Extract standardized academic years (e.g. '2026-27')."""
        detected: set[str] = set()

        for match in ACADEMIC_YEAR_PATTERN.finditer(full_text):
            start_year = match.group(1)
            end_year = match.group(2)
            # Normalize end year to 2 digits if 4 digits
            if len(end_year) == 4 and end_year.startswith("20"):
                end_year = end_year[2:]
            detected.add(f"{start_year}-{end_year}")

        return sorted(detected)
