"""Modular detector for SR University course codes."""

import re

from ingestion.models import DocumentElement
from ingestion.processors.detectors.base import BaseStructureDetector

# Common course code pattern:
# 1. 2 digits + 2-4 uppercase department letters + 3 digits + optional letter (e.g. 23CSE302T, 20EC201, 23AI101P)
# 2. 2-4 uppercase department letters + 3-4 digits (e.g. CS301, CSE302)
COURSE_CODE_PATTERN = re.compile(
    r"\b(?:[0-9]{2}[A-Z]{2,4}[0-9]{3}[A-Z]?|[A-Z]{2,4}[0-9]{3,4}[A-Z]?)\b"
)

# Negative filter for false positives that resemble course codes
FALSE_POSITIVES = {
    "HTTP404", "HTTP500", "ISO9001", "UTF8", "UTF16", "SHA256", "MD5", "PDF1", "DOCX1",
    "PAGE1", "PAGE2", "PAGE3", "SEC1", "SEC2", "PART1", "PART2"
}


class CourseCodeDetector(BaseStructureDetector):
    """Detects official university course codes from text and elements."""

    @property
    def name(self) -> str:
        return "course_code_detector"

    def detect(self, elements: list[DocumentElement], full_text: str) -> list[str]:
        """Extract unique course codes found across document elements."""
        detected: set[str] = set()

        for match in COURSE_CODE_PATTERN.finditer(full_text):
            code = match.group(0).strip().upper()
            if code not in FALSE_POSITIVES and not code.startswith("PAGE"):
                # Avoid matches that are purely numbers or standard acronyms
                if any(c.isdigit() for c in code) and any(c.isalpha() for c in code):
                    detected.add(code)

        return sorted(detected)
