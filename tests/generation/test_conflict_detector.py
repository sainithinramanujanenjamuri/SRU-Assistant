"""Unit tests for ConflictDetector evaluating date, regulation, and policy discrepancies."""

from generation.grounding.conflict_detector import ConflictDetector
from generation.models import RetrievedEvidence


def _make_ev(chunk_id: str, doc_name: str, text: str) -> RetrievedEvidence:
    return RetrievedEvidence(
        chunk_id=chunk_id,
        document_id=f"doc_{chunk_id}",
        document_name=doc_name,
        section_path="Section A",
        page_info="p. 1",
        text=text,
        score=0.9,
    )


class TestConflictDetector:
    """Test suite for cross-document conflict detection."""

    def test_conflicting_exam_dates(self):
        ev1 = _make_ev("c1", "calendar_v1.txt", "Mid-Semester Examination-I is on 15 September 2026.")
        ev2 = _make_ev("c2", "calendar_v2.txt", "Mid-Semester Examination-I is on 22 September 2026.")

        detector = ConflictDetector()
        report = detector.detect_conflicts([ev1, ev2])

        assert report.has_conflict is True
        assert report.conflict_type == "date_discrepancy"
        assert set(report.conflicting_sources) == {"calendar_v1.txt", "calendar_v2.txt"}
        assert len(report.details) >= 2

    def test_conflicting_course_regulations(self):
        ev1 = _make_ev("c1", "syllabus_v1.pdf", "Course 23CSE302T is administered under Regulation R23.")
        ev2 = _make_ev("c2", "handbook_old.pdf", "Course 23CSE302T is administered under Regulation R20.")

        detector = ConflictDetector()
        report = detector.detect_conflicts([ev1, ev2])

        assert report.has_conflict is True
        assert report.conflict_type == "regulation_discrepancy"
        assert "syllabus_v1.pdf" in report.conflicting_sources
        assert "handbook_old.pdf" in report.conflicting_sources

    def test_conflicting_attendance_policy(self):
        ev1 = _make_ev("c1", "student_code.pdf", "The minimum attendance requirement for examinations is 75%.")
        ev2 = _make_ev("c2", "department_memo.txt", "The minimum attendance requirement for examinations is 80%.")

        detector = ConflictDetector()
        report = detector.detect_conflicts([ev1, ev2])

        assert report.has_conflict is True
        assert report.conflict_type == "policy_discrepancy"

    def test_agreement_across_multiple_documents(self):
        ev1 = _make_ev("c1", "calendar.txt", "Mid-Semester Examination-I is scheduled for 15 September 2026.")
        ev2 = _make_ev("c2", "circular.pdf", "Mid-Semester Examination-I is scheduled for 15 September 2026.")

        detector = ConflictDetector()
        report = detector.detect_conflicts([ev1, ev2])

        assert report.has_conflict is False
        assert report.conflict_type is None
        assert report.conflicting_sources == []

    def test_duplicate_evidence_chunks(self):
        ev1 = _make_ev("c1", "calendar.txt", "Mid-Semester Examination-I: 12 September 2026.")
        ev2 = _make_ev("c2", "calendar.txt", "Mid-Semester Examination-I: 12 September 2026.")

        detector = ConflictDetector()
        report = detector.detect_conflicts([ev1, ev2])

        assert report.has_conflict is False

    def test_unrelated_distinct_topics_not_flagged(self):
        # Mid 1 vs Mid 2 have different dates, which is expected and not a conflict
        ev1 = _make_ev("c1", "calendar.txt", "Mid-Semester Examination-I is on 15 September 2026.")
        ev2 = _make_ev("c2", "calendar.txt", "Mid-Semester Examination-II is on 10 November 2026.")

        detector = ConflictDetector()
        report = detector.detect_conflicts([ev1, ev2])

        assert report.has_conflict is False

    def test_ambiguous_assertions_without_dates_or_entities(self):
        ev1 = _make_ev("c1", "doc1.txt", "Students should study regularly and prepare for tests.")
        ev2 = _make_ev("c2", "doc2.txt", "Library is open on weekdays from 9am to 5pm.")

        detector = ConflictDetector()
        report = detector.detect_conflicts([ev1, ev2])

        assert report.has_conflict is False
