"""Modular detector for academic semesters."""

import re

from ingestion.models import DocumentElement
from ingestion.processors.detectors.base import BaseStructureDetector

ROMAN_MAP = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V", "6": "VI", "7": "VII", "8": "VIII",
    "1st": "I", "2nd": "II", "3rd": "III", "4th": "IV", "5th": "V", "6th": "VI", "7th": "VII", "8th": "VIII",
    "first": "I", "second": "II", "third": "III", "fourth": "IV", "fifth": "V", "sixth": "VI", "seventh": "VII", "eighth": "VIII",
    "i": "I", "ii": "II", "iii": "III", "iv": "IV", "v": "V", "vi": "VI", "vii": "VII", "viii": "VIII",
}

SEMESTER_PATTERN = re.compile(
    r"\b(?:(?:Semester|Sem)\s*[-:]?\s*([I|V|X\d]+|1st|2nd|3rd|[4-8]th|first|second|third|fourth|fifth|sixth|seventh|eighth))|"
    r"\b(([I|V|X\d]+|1st|2nd|3rd|[4-8]th|first|second|third|fourth|fifth|sixth|seventh|eighth)\s+(?:Semester|Sem))\b",
    re.IGNORECASE,
)


class SemesterDetector(BaseStructureDetector):
    """Detects academic semester designations."""

    @property
    def name(self) -> str:
        return "semester_detector"

    def detect(self, elements: list[DocumentElement], full_text: str) -> list[str]:
        """Extract detected normalized semesters (e.g. 'Semester VII')."""
        detected: set[str] = set()

        for match in SEMESTER_PATTERN.finditer(full_text):
            val = (match.group(1) or match.group(3) or "").strip().lower()
            if val in ROMAN_MAP:
                detected.add(f"Semester {ROMAN_MAP[val]}")

        # Check for generic Odd/Even semester
        if re.search(r"\bOdd\s+Semester\b", full_text, re.IGNORECASE):
            detected.add("Odd Semester")
        if re.search(r"\bEven\s+Semester\b", full_text, re.IGNORECASE):
            detected.add("Even Semester")

        return sorted(detected)
