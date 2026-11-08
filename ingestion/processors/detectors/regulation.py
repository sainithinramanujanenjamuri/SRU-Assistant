"""Modular detector for SR University academic regulations (e.g. R23, R20, R18)."""

import re

from ingestion.models import DocumentElement
from ingestion.processors.detectors.base import BaseStructureDetector

REGULATION_PATTERN = re.compile(
    r"\b(?:Academic\s+Regulations?|Regulations?)?\s*R\s*[-–]?\s*(\d{2})\b",
    re.IGNORECASE,
)


class RegulationDetector(BaseStructureDetector):
    """Detects academic regulations (e.g. R23, R20) governing the syllabus or document."""

    @property
    def name(self) -> str:
        return "regulation_detector"

    def detect(self, elements: list[DocumentElement], full_text: str) -> list[str]:
        """Extract unique academic regulations found in the text."""
        detected: set[str] = set()

        for match in REGULATION_PATTERN.finditer(full_text):
            reg_num = match.group(1)
            detected.add(f"R{reg_num}")

        return sorted(detected)
