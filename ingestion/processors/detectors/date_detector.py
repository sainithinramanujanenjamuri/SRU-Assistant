"""Modular detector for academic calendar dates and date ranges."""

import re

from ingestion.models import DocumentElement
from ingestion.processors.detectors.base import BaseStructureDetector

MONTHS = (
    "January|February|March|April|May|June|July|August|September|October|November|December|"
    "Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec"
)

# Date range: e.g. "12 September 2026 – 16 September 2026" or "12-09-2026 to 16-09-2026"
DATE_RANGE_PATTERN = re.compile(
    rf"\b(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})\s+\d{{4}})\s*(?:[-–—]|to)\s*(\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})\s+\d{{4}})\b",
    re.IGNORECASE,
)

# Single date: e.g. "12 September 2026", "September 12, 2026", "12-09-2026", "12/09/2026"
SINGLE_DATE_PATTERN = re.compile(
    rf"\b(?:\d{{1,2}}(?:st|nd|rd|th)?\s+(?:{MONTHS})\s+\d{{4}}|(?:{MONTHS})\s+\d{{1,2}}(?:st|nd|rd|th)?,\s*\d{{4}}|\d{{1,2}}[-/.]\d{{1,2}}[-/.]\d{{4}})\b",
    re.IGNORECASE,
)


class DateDetector(BaseStructureDetector):
    """Detects calendar dates and ranges relevant to university academic schedules."""

    @property
    def name(self) -> str:
        return "date_detector"

    def detect(self, elements: list[DocumentElement], full_text: str) -> list[str]:
        """Extract detected dates and date ranges."""
        detected: set[str] = set()

        # Check date ranges first
        for match in DATE_RANGE_PATTERN.finditer(full_text):
            start_date = match.group(1).strip()
            end_date = match.group(2).strip()
            detected.add(f"{start_date} to {end_date}")

        # Check single dates
        for match in SINGLE_DATE_PATTERN.finditer(full_text):
            d_str = match.group(0).strip()
            detected.add(d_str)

        return sorted(detected)
