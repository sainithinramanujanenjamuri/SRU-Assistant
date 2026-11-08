"""Modular detector for academic document category classification."""

import re

from ingestion.models import DocumentElement
from ingestion.processors.detectors.base import BaseStructureDetector

CATEGORY_PATTERNS: list[tuple[re.Pattern, str]] = [
    (
        re.compile(r"\b(?:Academic\s+Calendar|Semester\s+Calendar|Almanac|Schedule\s+of\s+Events)\b", re.IGNORECASE),
        "academic_calendar",
    ),
    (
        re.compile(r"\b(?:Examination\s+(?:Time\s*Table|Schedule|Date\s*Sheet)|Exam\s+Timetable)\b", re.IGNORECASE),
        "exam_schedule",
    ),
    (
        re.compile(r"\b(?:Course\s+Structure|Syllabus|Curriculum|Scheme\s+of\s+Instruction|Course\s+Description)\b", re.IGNORECASE),
        "syllabus",
    ),
    (
        re.compile(r"\b(?:Examination\s+Guidelines?|Instructions?\s+to\s+Candidates?|Malpractice\s+Rules?)\b", re.IGNORECASE),
        "exam_guidelines",
    ),
    (
        re.compile(r"\b(?:Department\s+Notice|Circular|Office\s+Order|Student\s+Notice)\b", re.IGNORECASE),
        "department_notice",
    ),
]


class DocumentCategoryDetector(BaseStructureDetector):
    """Detects institutional category for an academic document."""

    @property
    def name(self) -> str:
        return "document_category_detector"

    def detect(self, elements: list[DocumentElement], full_text: str) -> list[str]:
        """Classify document category based on explicit evidence in title and text."""
        detected: set[str] = set()

        # Prioritize top 5 elements (header/title area)
        top_text = " ".join(e.content for e in elements[:5])
        for pattern, cat in CATEGORY_PATTERNS:
            if pattern.search(top_text):
                detected.add(cat)

        # Fallback to full text if not detected in top lines
        if not detected:
            for pattern, cat in CATEGORY_PATTERNS:
                if pattern.search(full_text):
                    detected.add(cat)

        return sorted(detected)
