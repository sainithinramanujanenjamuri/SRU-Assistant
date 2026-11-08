"""AcademicQueryAnalyzer for deterministic, non-destructive entity and intent extraction."""
from __future__ import annotations


import re
from typing import Any

from retrieval.models import QueryAnalysisResult


class AcademicQueryAnalyzer:
    """Extracts institutional entities, intent, and suggested filters from student queries.


    Design Principles:
    1. Deterministic: Rule- and regex-based, zero random sampling, reproducible across runs.
    2. Conservative: Only extracts entities that have high-confidence pattern matches.
       Never invents entities or guesses when absent.
    3. Non-Destructive: Emits suggested filters and classification metadata for retrieval hints,
       without forcing document exclusions or pruning global evidence.
    """

    # Course codes: e.g. 23CSE302T, 23EC301, CS302, 20CS101
    COURSE_CODE_PATTERN = re.compile(
        r"\b(?:2[0-9])?[A-Z]{2,4}\d{3}[A-Z]?\b",
        re.IGNORECASE,
    )

    # Regulation identifiers: e.g. R23, R20, R18
    REGULATION_PATTERN = re.compile(
        r"\b[Rr](\d{2})\b",
    )

    # Academic years: e.g. 2026-27, 2026-2027, 2025-26
    ACADEMIC_YEAR_PATTERN = re.compile(
        r"\b(20\d{2})[-/](\d{2}|\d{4})\b",
    )

    # Specific date patterns: e.g. "12 September 2026", "10 August 2026"
    DATE_PATTERN = re.compile(
        r"\b\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b",
        re.IGNORECASE,
    )

    # Semester patterns and normalization table
    SEMESTER_PATTERNS = [
        (re.compile(r"\b(?:semester\s+)?(viii|8)(?:th)?(?:\s+semester)?\b", re.IGNORECASE), "Semester VIII"),
        (re.compile(r"\b(?:semester\s+)?(vii|7)(?:th)?(?:\s+semester)?\b", re.IGNORECASE), "Semester VII"),
        (re.compile(r"\b(?:semester\s+)?(vi|6)(?:th)?(?:\s+semester)?\b", re.IGNORECASE), "Semester VI"),
        (re.compile(r"\b(?:semester\s+)?(v|5)(?:th)?(?:\s+semester)?\b", re.IGNORECASE), "Semester V"),
        (re.compile(r"\b(?:semester\s+)?(iv|4)(?:th)?(?:\s+semester)?\b", re.IGNORECASE), "Semester IV"),
        (re.compile(r"\b(?:semester\s+)?(iii|3)(?:rd)?(?:\s+semester)?\b", re.IGNORECASE), "Semester III"),
        (re.compile(r"\b(?:semester\s+)?(ii|2)(?:nd)?(?:\s+semester)?\b", re.IGNORECASE), "Semester II"),
        (re.compile(r"\b(?:semester\s+)?(i|1)(?:st)?(?:\s+semester)?\b", re.IGNORECASE), "Semester I"),
    ]

    # Department aliases and canonical forms
    DEPARTMENT_MAP = {
        "cse": "Computer Science and Engineering",
        "computer science": "Computer Science and Engineering",
        "computer science and engineering": "Computer Science and Engineering",
        "ece": "Electronics and Communication Engineering",
        "electronics": "Electronics and Communication Engineering",
        "electronics and communication": "Electronics and Communication Engineering",
        "electronics and communication engineering": "Electronics and Communication Engineering",
        "eee": "Electrical and Electronics Engineering",
        "electrical": "Electrical and Electronics Engineering",
        "mech": "Mechanical Engineering",
        "mechanical": "Mechanical Engineering",
        "mechanical engineering": "Mechanical Engineering",
        "civil": "Civil Engineering",
        "civil engineering": "Civil Engineering",
    }

    # Program aliases
    PROGRAM_MAP = {
        "b.tech": "B.Tech",
        "btech": "B.Tech",
        "b tech": "B.Tech",
        "m.tech": "M.Tech",
        "mtech": "M.Tech",
        "m tech": "M.Tech",
        "mba": "MBA",
        "mca": "MCA",
        "ph.d": "Ph.D",
        "phd": "Ph.D",
    }

    # Examination terms
    EXAMINATION_TERMS = [
        "First Mid Examinations",
        "Second Mid Examinations",
        "Mid-Semester Examination I",
        "Mid-Semester Examination II",
        "End Semester Examinations",
        "End-Semester Examination",
        "Mid Examinations",
        "Mid Examination",
        "Mid-Semester Examination",
        "Classwork",
    ]

    # Academic Acronym and Shorthand Expansions (Phase 12)
    ACRONYM_EXPANSIONS = [
        (re.compile(r"\bmid[\s\-_]*1\b", re.IGNORECASE), "Mid-Semester Examination I"),
        (re.compile(r"\bmid[\s\-_]*2\b", re.IGNORECASE), "Mid-Semester Examination II"),
        (re.compile(r"\bmid[\s\-_]*i\b", re.IGNORECASE), "Mid-Semester Examination I"),
        (re.compile(r"\bmid[\s\-_]*ii\b", re.IGNORECASE), "Mid-Semester Examination II"),
        (re.compile(r"\bsee\b", re.IGNORECASE), "Semester End Examinations"),
        (re.compile(r"\bcie\b", re.IGNORECASE), "Continuous Internal Evaluation"),
        (re.compile(r"\bdl\b", re.IGNORECASE), "Deep Learning 23CS401"),
        (re.compile(r"\bnlp\b", re.IGNORECASE), "Natural Language Processing 23CS411"),
        (re.compile(r"\bteam[\s\-_]*235\b", re.IGNORECASE), "Capstone Project Team 235"),
        (re.compile(r"\battendance\b", re.IGNORECASE), "attendance 75% condonation detention"),
        (re.compile(r"\bcondonation\b", re.IGNORECASE), "condonation 65% medical grounds"),
        (re.compile(r"\bdetention\b", re.IGNORECASE), "detained below 65% attendance"),
        (re.compile(r"\bcredits?\b", re.IGNORECASE), "160 academic credits degree"),
    ]

    def analyze(self, query: str) -> QueryAnalysisResult:

        """Analyze user query and return extracted characteristics and suggested filters."""
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")

        cleaned = query.strip()
        lower_q = cleaned.lower()

        entities: dict[str, Any] = {}
        suggested_filters: dict[str, Any] = {}
        normalized_values: dict[str, str] = {}

        # 1. Course code extraction
        course_code: str | None = None
        for match in self.COURSE_CODE_PATTERN.finditer(cleaned):
            token = match.group(0)
            # Filter out non-code false positives like "R23" or dates
            if re.match(r"^R\d{2}$", token, re.IGNORECASE):
                continue
            course_code = token.upper()
            entities["course_code"] = course_code
            normalized_values["course_code"] = course_code
            break

        # 2. Regulation extraction
        regulation: str | None = None
        reg_match = self.REGULATION_PATTERN.search(cleaned)
        if reg_match:
            regulation = f"R{reg_match.group(1)}"
            entities["regulation"] = regulation
            suggested_filters["regulation"] = regulation
            normalized_values["regulation"] = regulation

        # 3. Academic year extraction
        academic_year: str | None = None
        ay_match = self.ACADEMIC_YEAR_PATTERN.search(cleaned)
        if ay_match:
            y1, y2 = ay_match.group(1), ay_match.group(2)
            if len(y2) == 4:
                y2 = y2[-2:]
            academic_year = f"{y1}-{y2}"
            entities["academic_year"] = academic_year
            suggested_filters["academic_year"] = academic_year
            normalized_values["academic_year"] = academic_year

        # 4. Department extraction
        department: str | None = None
        # Check longest keys first
        for alias in sorted(self.DEPARTMENT_MAP.keys(), key=len, reverse=True):
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, lower_q):
                department = self.DEPARTMENT_MAP[alias]
                entities["department"] = department
                suggested_filters["department"] = department
                normalized_values["department"] = department
                break

        # 5. Program extraction
        program: str | None = None
        for alias in sorted(self.PROGRAM_MAP.keys(), key=len, reverse=True):
            pattern = rf"\b{re.escape(alias)}\b"
            if re.search(pattern, lower_q):
                program = self.PROGRAM_MAP[alias]
                entities["program"] = program
                suggested_filters["program"] = program
                normalized_values["program"] = program
                break

        # 6. Semester extraction
        semester: str | None = None
        # Check explicit semester mentions
        if "sem" in lower_q or "semester" in lower_q:
            for pat, canon in self.SEMESTER_PATTERNS:
                if pat.search(lower_q):
                    semester = canon
                    entities["semester"] = semester
                    suggested_filters["semester"] = semester
                    normalized_values["semester"] = semester
                    break

        # 7. Dates extraction
        dates_found: list[str] = []
        for m in self.DATE_PATTERN.finditer(cleaned):
            dates_found.append(m.group(0))
        if dates_found:
            entities["dates"] = dates_found

        # 8. Examination terms extraction
        exam_terms_found: list[str] = []
        for term in self.EXAMINATION_TERMS:
            if re.search(rf"\b{re.escape(term)}\b", cleaned, re.IGNORECASE):
                exam_terms_found.append(term)
        if exam_terms_found:
            entities["examination_terms"] = exam_terms_found

        # 9. Inferred document type
        document_type: str | None = None
        if "syllabus" in lower_q or "curriculum" in lower_q or "course overview" in lower_q:
            document_type = "syllabus"
        elif "calendar" in lower_q or "classwork" in lower_q or "commence" in lower_q:
            document_type = "academic_calendar"
        elif "regulation" in lower_q or "regulations" in lower_q:
            document_type = "regulations"
        elif "exam" in lower_q or "examination" in lower_q:
            # If dates or calendar are mentioned, it may be calendar or examination
            if "when" in lower_q or "date" in lower_q or "schedule" in lower_q:
                document_type = "academic_calendar"
            else:
                document_type = "examination"

        if document_type:
            entities["document_type"] = document_type
            # We do NOT add document_type to suggested_filters automatically
            # because calendar contains examination dates!

        # 10. Question type classification
        question_type = "general"
        if any(w in lower_q for w in ["when", "date", "schedule", "schedule", "commence", "start", "timeline"]):
            question_type = "examination_date"
        elif any(w in lower_q for w in ["learn", "topic", "objective", "content", "unit", "module", "syllabus"]):
            question_type = "syllabus_content"
        elif any(w in lower_q for w in ["grade", "grading", "mark", "marks", "credit", "credits", "gpa", "cgpa"]):
            question_type = "grading_policy"
        elif any(w in lower_q for w in ["rule", "rules", "detention", "attendance", "minimum", "eligibility"]):
            question_type = "regulation_rule"

        # 11. Query Expansion (Phase 12)
        expansion_terms: list[str] = []
        for pattern, canon_term in self.ACRONYM_EXPANSIONS:
            if pattern.search(cleaned):
                expansion_terms.append(canon_term)

        expanded_query: str = cleaned
        if expansion_terms:
            expanded_query = f"{cleaned} ({' '.join(expansion_terms)})"

        return QueryAnalysisResult(
            query=cleaned,
            department=department,
            program=program,
            semester=semester,
            academic_year=academic_year,
            document_type=document_type,
            course_code=course_code,
            regulation=regulation,
            question_type=question_type,
            dates=dates_found,
            examination_terms=exam_terms_found,
            detected_entities=entities,
            suggested_filters=suggested_filters,
            normalized_values=normalized_values,
            expanded_query=expanded_query,
        )

