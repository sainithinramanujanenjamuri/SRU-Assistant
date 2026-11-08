"""Modular detector for examination events and schedules."""

import re

from ingestion.models import DocumentElement
from ingestion.processors.detectors.base import BaseStructureDetector

EXAM_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"\b(?:Mid[- ]Semester\s+(?:Examination|Exam)\s*[-–]?\s*I\b|Mid[- ]1\b|First\s+Mid)", re.IGNORECASE),
        "Mid-Semester Examination I",
    ),
    (
        re.compile(r"\b(?:Mid[- ]Semester\s+(?:Examination|Exam)\s*[-–]?\s*II\b|Mid[- ]2\b|Second\s+Mid)", re.IGNORECASE),
        "Mid-Semester Examination II",
    ),
    (
        re.compile(r"\b(?:End[- ]Semester\s+(?:Examinations?|Exams?)|Regular\s+Examinations?|Semester\s+End\s+Exams?)\b", re.IGNORECASE),
        "End Semester Examinations",
    ),
    (
        re.compile(r"\b(?:Supplementary\s+Examinations?|Supply\s+Exams?)\b", re.IGNORECASE),
        "Supplementary Examinations",
    ),
    (
        re.compile(r"\b(?:Practical\s+Examinations?|Lab\s+Examinations?|Laboratory\s+Exams?)\b", re.IGNORECASE),
        "Practical Examinations",
    ),
]


class ExaminationDetector(BaseStructureDetector):
    """Detects examination types and schedules mentioned in academic documents."""

    @property
    def name(self) -> str:
        return "examination_detector"

    def detect(self, elements: list[DocumentElement], full_text: str) -> list[str]:
        """Extract matched standardized examination types."""
        detected: set[str] = set()

        for pattern, standard_name in EXAM_PATTERNS:
            if pattern.search(full_text):
                detected.add(standard_name)

        return sorted(detected)
