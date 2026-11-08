"""Unit tests for AcademicQueryAnalyzer (Phase 6)."""

import pytest

from retrieval.query.analyzer import AcademicQueryAnalyzer


@pytest.fixture
def analyzer() -> AcademicQueryAnalyzer:
    return AcademicQueryAnalyzer()


def test_course_code_extraction(analyzer: AcademicQueryAnalyzer):
    res = analyzer.analyze("What are the prerequisites for course 23CSE302T?")
    assert res.course_code == "23CSE302T"
    assert res.detected_entities.get("course_code") == "23CSE302T"
    assert res.normalized_values.get("course_code") == "23CSE302T"


def test_regulation_extraction(analyzer: AcademicQueryAnalyzer):
    res = analyzer.analyze("Explain the promotion rules under R23 regulations.")
    assert res.regulation == "R23"
    assert res.suggested_filters.get("regulation") == "R23"


def test_academic_year_extraction(analyzer: AcademicQueryAnalyzer):
    res = analyzer.analyze("Show me the calendar for session 2026-27.")
    assert res.academic_year == "2026-27"
    assert res.suggested_filters.get("academic_year") == "2026-27"


def test_semester_extraction_and_normalization(analyzer: AcademicQueryAnalyzer):
    # Roman numeral
    res1 = analyzer.analyze("When do Semester VII classes commence?")
    assert res1.semester == "Semester VII"

    # Digit
    res2 = analyzer.analyze("What subjects are in 7th sem?")
    assert res2.semester == "Semester VII"

    # Word 'sem' + roman
    res3 = analyzer.analyze("Syllabus for sem 3")
    assert res3.semester == "Semester III"


def test_department_extraction_and_alias(analyzer: AcademicQueryAnalyzer):
    # Short acronym
    res1 = analyzer.analyze("Who is the HOD of CSE?")
    assert res1.department == "Computer Science and Engineering"
    assert res1.suggested_filters.get("department") == "Computer Science and Engineering"

    # Full name
    res2 = analyzer.analyze("Guidelines for Electronics and Communication Engineering")
    assert res2.department == "Electronics and Communication Engineering"


def test_program_extraction(analyzer: AcademicQueryAnalyzer):
    res1 = analyzer.analyze("Curriculum structure for B.Tech students")
    assert res1.program == "B.Tech"
    assert res1.suggested_filters.get("program") == "B.Tech"

    res2 = analyzer.analyze("Fees structure for MBA 2026-27")
    assert res2.program == "MBA"


def test_date_and_exam_term_extraction(analyzer: AcademicQueryAnalyzer):
    query = "Is Mid-Semester Examination I scheduled on 12 September 2026?"
    res = analyzer.analyze(query)
    assert "12 September 2026" in res.dates
    assert any("Mid-Semester Examination I" in term for term in res.examination_terms)
    assert res.question_type == "examination_date"


def test_question_type_classification(analyzer: AcademicQueryAnalyzer):
    res_date = analyzer.analyze("When are the mid exams conducted?")
    assert res_date.question_type == "examination_date"

    res_syl = analyzer.analyze("What topics will students learn in module 2?")
    assert res_syl.question_type == "syllabus_content"

    res_grade = analyzer.analyze("What are the minimum passing credits and GPA?")
    assert res_grade.question_type == "grading_policy"

    res_rule = analyzer.analyze("What is the minimum attendance rule?")
    assert res_rule.question_type == "regulation_rule"

    res_gen = analyzer.analyze("Tell me about SR University.")
    assert res_gen.question_type == "general"


def test_conservative_behavior_no_fabrication(analyzer: AcademicQueryAnalyzer):
    # A generic query with no entities should yield None without guessing
    res = analyzer.analyze("Hello there, can you help me?")
    assert res.course_code is None
    assert res.regulation is None
    assert res.department is None
    assert res.program is None
    assert res.semester is None
    assert res.academic_year is None
    assert res.dates == []
    assert res.examination_terms == []
    assert res.suggested_filters == {}


def test_deterministic_repeatability(analyzer: AcademicQueryAnalyzer):
    query = "When are the B.Tech CSE 7th semester mid exams under R23?"
    res1 = analyzer.analyze(query)
    res2 = analyzer.analyze(query)
    assert res1.model_dump() == res2.model_dump()


def test_empty_query_raises_value_error(analyzer: AcademicQueryAnalyzer):
    with pytest.raises(ValueError):
        analyzer.analyze("")
    with pytest.raises(ValueError):
        analyzer.analyze("   ")
