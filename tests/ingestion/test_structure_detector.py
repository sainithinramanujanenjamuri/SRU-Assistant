"""Unit tests for individual and composite modular academic structure detectors."""

from ingestion.models import DocumentElement, ElementProvenance, ElementType
from ingestion.processors.detectors import (
    AcademicYearDetector,
    CourseCodeDetector,
    DateDetector,
    DepartmentDetector,
    DocumentCategoryDetector,
    ExaminationDetector,
    RegulationDetector,
    SemesterDetector,
)
from ingestion.processors.structure_detector import StructureDetector


def make_test_element(text: str) -> DocumentElement:
    """Helper to create dummy element for detector tests."""
    return DocumentElement(
        element_id="test_01",
        element_type=ElementType.PARAGRAPH,
        content=text,
        provenance=ElementProvenance(
            document_id="test_doc",
            source_file="test.txt",
            structural_index=1,
        ),
    )


def test_course_code_detector() -> None:
    """Verify detection of university course codes and rejection of false positives."""
    text = "Students registered for 23CSE302T and 20EC201 must refer to CS301. Do not encounter HTTP404 or UTF8."
    detector = CourseCodeDetector()
    results = detector.detect([make_test_element(text)], text)

    assert "23CSE302T" in results
    assert "20EC201" in results
    assert "CS301" in results
    assert "HTTP404" not in results
    assert "UTF8" not in results


def test_regulation_detector() -> None:
    """Verify detection of SRU academic regulations."""
    text = "These academic guidelines are framed under Academic Regulations R-23 and R20."
    detector = RegulationDetector()
    results = detector.detect([make_test_element(text)], text)

    assert "R23" in results
    assert "R20" in results


def test_department_detector() -> None:
    """Verify detection of departments by name and acronym."""
    text = "Department of Computer Science and Engineering offers courses alongside Mechanical Engineering and ECE."
    detector = DepartmentDetector()
    results = detector.detect([make_test_element(text)], text)

    assert "Computer Science and Engineering" in results
    assert "Mechanical Engineering" in results
    assert "Electronics and Communication Engineering" in results


def test_semester_detector() -> None:
    """Verify detection and normalization of academic semesters."""
    text = "Registration is open for Semester VII, 1st Semester, and Odd Semester students."
    detector = SemesterDetector()
    results = detector.detect([make_test_element(text)], text)

    assert "Semester VII" in results
    assert "Semester I" in results
    assert "Odd Semester" in results


def test_academic_year_detector() -> None:
    """Verify detection and normalization of academic years."""
    text = "The almanac applies to the Academic Year 2026-27 and prior year 2025-2026."
    detector = AcademicYearDetector()
    results = detector.detect([make_test_element(text)], text)

    assert "2026-27" in results
    assert "2025-26" in results


def test_examination_detector() -> None:
    """Verify detection of university examination schedules."""
    text = "Mid-Semester Examination I will be followed by End Semester Examinations and Supplementary Examinations."
    detector = ExaminationDetector()
    results = detector.detect([make_test_element(text)], text)

    assert "Mid-Semester Examination I" in results
    assert "End Semester Examinations" in results
    assert "Supplementary Examinations" in results


def test_date_detector() -> None:
    """Verify detection of single dates and date ranges."""
    text = "Mid exams are scheduled from 12 September 2026 to 16 September 2026. Results on 30-09-2026."
    detector = DateDetector()
    results = detector.detect([make_test_element(text)], text)

    assert any("12 September 2026 to 16 September 2026" in d for d in results)
    assert any("30-09-2026" in d for d in results)


def test_document_category_detector() -> None:
    """Verify classification of document categories."""
    calendar_text = "SR University Almanac / Academic Calendar for 2026-27"
    syllabus_text = "Course Structure and Syllabus - Department of CSE"
    exam_text = "Examination Time Table for Regular Examinations"

    detector = DocumentCategoryDetector()
    assert "academic_calendar" in detector.detect([make_test_element(calendar_text)], calendar_text)
    assert "syllabus" in detector.detect([make_test_element(syllabus_text)], syllabus_text)
    assert "exam_schedule" in detector.detect([make_test_element(exam_text)], exam_text)


def test_composite_structure_detector() -> None:
    """Verify composite StructureDetector combines all modular detectors and extracts headings."""
    text = (
        "# SR University Academic Calendar 2026-27\n"
        "Department of Computer Science and Engineering\n"
        "Regulation R23 - Semester VII\n"
        "Course: 23CSE302T\n"
        "Mid-Semester Examination I: 12 September 2026 to 16 September 2026"
    )

    elem1 = DocumentElement(
        element_id="elem_01",
        element_type=ElementType.HEADING,
        content="SR University Academic Calendar 2026-27",
        provenance=ElementProvenance(document_id="doc1", source_file="cal.txt", structural_index=1),
    )
    elem2 = DocumentElement(
        element_id="elem_02",
        element_type=ElementType.PARAGRAPH,
        content=text,
        provenance=ElementProvenance(document_id="doc1", source_file="cal.txt", structural_index=2),
    )

    detector = StructureDetector()
    structures = detector.detect_structures([elem1, elem2], text)

    assert "23CSE302T" in structures.course_codes
    assert "R23" in structures.regulations
    assert "Computer Science and Engineering" in structures.departments
    assert "Semester VII" in structures.semesters
    assert "2026-27" in structures.academic_years
    assert "Mid-Semester Examination I" in structures.examinations
    assert len(structures.headings) == 1
    assert structures.headings[0]["title"] == "SR University Academic Calendar 2026-27"
