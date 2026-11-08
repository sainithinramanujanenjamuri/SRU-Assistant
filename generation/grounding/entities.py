"""Academic entity extraction and normalization utilities for grounding verification.

Extracts and normalizes university domain entities (course codes, regulations,
academic sessions, calendar dates, examination types, and semesters)
to support deterministic entity containment checking and conflict detection.
"""

import datetime
import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AcademicEntity:
    """Represents an extracted academic entity with raw and normalized forms."""

    raw_entity: str
    normalized_entity: str
    entity_type: str  # 'course_code', 'regulation', 'academic_year', 'date', 'exam_type', 'semester', 'department'


class AcademicEntityExtractor:
    """Deterministic, rule-based extractor and normalizer for university academic entities."""

    # Course codes: e.g. 23CSE302T, 20ME101, 18ECE401
    COURSE_CODE_PATTERN = re.compile(r"\b\d{2}[A-Z]{2,4}\d{3}[A-Z]?\b", re.IGNORECASE)

    # Regulation codes: e.g. R23, R-23, R18
    REGULATION_PATTERN = re.compile(r"\b[Rr]-?(\d{2})\b")

    # Academic years: e.g. 2026-27, 2026–27, 2026/27, 2026-2027 (not followed by another date part)
    ACADEMIC_YEAR_PATTERN = re.compile(r"\b(20\d{2})[-–/](20\d{2}|\d{2})\b(?![/-]\d{1,2})")

    # Examination types: e.g. Mid-Semester Examination-I, Mid 1, End-Sem Exam
    EXAM_TYPE_PATTERNS = [
        (re.compile(r"\bmid[- ](?:semester\s+)?exam(?:ination)?[- ]?(?:i|1)\b", re.IGNORECASE), "mid_exam_1"),
        (re.compile(r"\bmid[- ](?:semester\s+)?exam(?:ination)?[- ]?(?:ii|2)\b", re.IGNORECASE), "mid_exam_2"),
        (re.compile(r"\bend[- ](?:semester\s+)?exam(?:ination)?\b", re.IGNORECASE), "end_exam"),
        (re.compile(r"\bsupplementary\s+exam(?:ination)?\b", re.IGNORECASE), "supplementary_exam"),
    ]

    # Semester patterns: Semester VII, Sem 7, 7th Semester
    SEMESTER_PATTERN = re.compile(
        r"\b(?:semester\s+(vii|viii|vi|iv|v|iii|ii|i|\d+)|sem\s+(\d+|vii|viii|vi|iv|v|iii|ii|i)|(\d+)(?:st|nd|rd|th)\s+semester)\b",
        re.IGNORECASE,
    )

    # Date regexes:
    # 1) DD Month YYYY or Month DD, YYYY: 15 September 2026 / September 15, 2026
    MONTH_NAMES = r"(?:january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|sept|oct|nov|dec)"
    DATE_WORDS_PATTERN = re.compile(
        rf"\b(\d{{1,2}})\s+({MONTH_NAMES})\s+(20\d{{2}})\b|\b({MONTH_NAMES})\s+(\d{{1,2}}),?\s+(20\d{{2}})\b",
        re.IGNORECASE,
    )

    # 2) Numerical dates: YYYY-MM-DD, DD-MM-YYYY, DD/MM/YYYY
    DATE_NUMERIC_PATTERN = re.compile(
        r"\b(20\d{2})[-/.](0?[1-9]|1[0-2])[-/.](0?[1-9]|[12]\d|3[01])\b|"
        r"\b(0?[1-9]|[12]\d|3[01])[-/.](0?[1-9]|1[0-2])[-/.](20\d{2})\b"
    )

    MONTH_MAP = {
        "jan": 1, "january": 1, "feb": 2, "february": 2, "mar": 3, "march": 3,
        "apr": 4, "april": 4, "may": 5, "jun": 6, "june": 6, "jul": 7, "july": 7,
        "aug": 8, "august": 8, "sep": 9, "sept": 9, "september": 9, "oct": 10, "october": 10,
        "nov": 11, "november": 11, "dec": 12, "december": 12,
    }

    ROMAN_TO_INT = {
        "i": "1", "ii": "2", "iii": "3", "iv": "4", "v": "5", "vi": "6", "vii": "7", "viii": "8"
    }

    @classmethod
    def extract_entities(cls, text: str) -> list[AcademicEntity]:
        """Extract and normalize all recognized academic entities from text."""
        if not text:
            return []

        entities: list[AcademicEntity] = []
        seen: set[tuple[str, str]] = set()

        # 1. Course codes
        for m in cls.COURSE_CODE_PATTERN.finditer(text):
            raw = m.group(0)
            norm = raw.upper()
            key = ("course_code", norm)
            if key not in seen:
                seen.add(key)
                entities.append(AcademicEntity(raw_entity=raw, normalized_entity=norm, entity_type="course_code"))

        # 2. Regulations
        for m in cls.REGULATION_PATTERN.finditer(text):
            raw = m.group(0)
            norm = f"R{m.group(1)}"
            key = ("regulation", norm)
            if key not in seen:
                seen.add(key)
                entities.append(AcademicEntity(raw_entity=raw, normalized_entity=norm, entity_type="regulation"))

        # 3. Academic years
        for m in cls.ACADEMIC_YEAR_PATTERN.finditer(text):
            raw = m.group(0)
            y1 = m.group(1)
            y2 = m.group(2)
            if len(y2) == 4:
                y2 = y2[2:]
            norm = f"{y1}-{y2}"
            key = ("academic_year", norm)
            if key not in seen:
                seen.add(key)
                entities.append(AcademicEntity(raw_entity=raw, normalized_entity=norm, entity_type="academic_year"))

        # 4. Exam types
        for pattern, norm_code in cls.EXAM_TYPE_PATTERNS:
            for m in pattern.finditer(text):
                raw = m.group(0)
                key = ("exam_type", norm_code)
                if key not in seen:
                    seen.add(key)
                    entities.append(AcademicEntity(raw_entity=raw, normalized_entity=norm_code, entity_type="exam_type"))

        # 5. Semesters
        for m in cls.SEMESTER_PATTERN.finditer(text):
            raw = m.group(0)
            sem_val = m.group(1) or m.group(2) or m.group(3)
            val_lower = sem_val.lower()
            norm_sem = cls.ROMAN_TO_INT.get(val_lower, val_lower)
            norm = f"Semester {norm_sem}"
            key = ("semester", norm)
            if key not in seen:
                seen.add(key)
                entities.append(AcademicEntity(raw_entity=raw, normalized_entity=norm, entity_type="semester"))

        # 6. Word-based dates: e.g. 15 September 2026 or September 15, 2026
        for m in cls.DATE_WORDS_PATTERN.finditer(text):
            raw = m.group(0)
            if m.group(1):  # 15 September 2026
                day = int(m.group(1))
                month = cls.MONTH_MAP.get(m.group(2).lower(), 1)
                year = int(m.group(3))
            else:  # September 15, 2026
                month = cls.MONTH_MAP.get(m.group(4).lower(), 1)
                day = int(m.group(5))
                year = int(m.group(6))

            try:
                dt = datetime.date(year, month, day)
                norm = dt.strftime("%Y-%m-%d")
                key = ("date", norm)
                if key not in seen:
                    seen.add(key)
                    entities.append(AcademicEntity(raw_entity=raw, normalized_entity=norm, entity_type="date"))
            except ValueError:
                pass

        # 7. Numeric dates: e.g. 2026-09-15 or 15-09-2026
        for m in cls.DATE_NUMERIC_PATTERN.finditer(text):
            raw = m.group(0)
            if m.group(1):  # YYYY-MM-DD
                year = int(m.group(1))
                month = int(m.group(2))
                day = int(m.group(3))
            else:  # DD-MM-YYYY
                day = int(m.group(4))
                month = int(m.group(5))
                year = int(m.group(6))

            try:
                dt = datetime.date(year, month, day)
                norm = dt.strftime("%Y-%m-%d")
                key = ("date", norm)
                if key not in seen:
                    seen.add(key)
                    entities.append(AcademicEntity(raw_entity=raw, normalized_entity=norm, entity_type="date"))
            except ValueError:
                pass

        return entities

    @classmethod
    def normalize_string(cls, text: str) -> str:
        """Lightweight non-destructive normalization for whitespace and casing comparisons."""
        return re.sub(r"\s+", " ", text).strip().lower()
