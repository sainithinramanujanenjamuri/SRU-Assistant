"""Modular detector for academic departments and disciplines."""

import re

from ingestion.models import DocumentElement
from ingestion.processors.detectors.base import BaseStructureDetector

DEPARTMENT_MAP: list[tuple[re.Pattern, str]] = [
    (
        re.compile(
            r"\b(?:Department\s+of\s+)?Computer\s+Science(?:\s+(?:and|&)\s+Engineering)?\b|\bCSE\b",
            re.IGNORECASE,
        ),
        "Computer Science and Engineering",
    ),
    (
        re.compile(
            r"\b(?:Department\s+of\s+)?Electronics\s+(?:and|&)\s+Communication(?:\s+Engineering)?\b|\bECE\b",
            re.IGNORECASE,
        ),
        "Electronics and Communication Engineering",
    ),
    (
        re.compile(
            r"\b(?:Department\s+of\s+)?Mechanical\s+Engineering\b|\bMECH\b",
            re.IGNORECASE,
        ),
        "Mechanical Engineering",
    ),
    (
        re.compile(
            r"\b(?:Department\s+of\s+)?Civil\s+Engineering\b|\bCIVIL\b",
            re.IGNORECASE,
        ),
        "Civil Engineering",
    ),
    (
        re.compile(
            r"\b(?:Department\s+of\s+)?Electrical\s+(?:and|&)\s+Electronics(?:\s+Engineering)?\b|\bEEE\b",
            re.IGNORECASE,
        ),
        "Electrical and Electronics Engineering",
    ),
    (
        re.compile(
            r"\b(?:Department\s+of\s+)?Artificial\s+Intelligence(?:\s+(?:and|&)\s+Data\s+Science)?\b|\bAI(?:&|and)?DS\b|\bAIML\b",
            re.IGNORECASE,
        ),
        "Artificial Intelligence and Machine Learning",
    ),
    (
        re.compile(r"\b(?:Department\s+of\s+)?Information\s+Technology\b|\bIT\b", re.IGNORECASE),
        "Information Technology",
    ),
    (
        re.compile(r"\b(?:School\s+of\s+Business|Department\s+of\s+Management|\bMBA\b)", re.IGNORECASE),
        "Business Administration",
    ),
]


class DepartmentDetector(BaseStructureDetector):
    """Detects academic departments mentioned in the document."""

    @property
    def name(self) -> str:
        return "department_detector"

    def detect(self, elements: list[DocumentElement], full_text: str) -> list[str]:
        """Extract matched standardized department names."""
        detected: set[str] = set()

        for pattern, standard_name in DEPARTMENT_MAP:
            if pattern.search(full_text):
                detected.add(standard_name)

        return sorted(detected)
