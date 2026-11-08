"""Unit tests for GroundingValidator checking entity containment, statement support, and remediation."""

from generation.grounding.validator import GroundingValidator
from generation.models import RetrievedEvidence
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK


def _make_ev(text: str) -> RetrievedEvidence:
    return RetrievedEvidence(
        chunk_id="c_test",
        document_id="doc_test",
        document_name="official_rules.pdf",
        text=text,
        score=0.9,
    )


class TestGroundingValidator:
    """Test suite for GroundingValidator."""

    def test_fully_grounded_answer(self):
        ev = _make_ev("Mid-Semester Examination-I is on 15 September 2026 for course 23CSE302T under R23.")
        answer = "The Mid-Semester Examination-I is on 15 September 2026 for course 23CSE302T under R23."

        validator = GroundingValidator(strict_mode=False)
        res, final_ans = validator.validate(answer, [ev])

        assert res.is_grounded is True
        assert res.faithfulness_score > 0.8
        assert res.ungrounded_entities == []
        assert res.remediation_applied is False
        assert final_ans == answer

    def test_unsupported_course_code(self):
        ev = _make_ev("Mid-Semester Examination-I is on 15 September 2026 for course 23CSE302T.")
        # Hallucinated course 99MEC999Z
        answer = "The examination is scheduled for course 99MEC999Z on 15 September 2026."

        validator = GroundingValidator(strict_mode=False)
        res, _ = validator.validate(answer, [ev])

        assert res.is_grounded is False
        assert any("99MEC999Z" in e for e in res.ungrounded_entities)

    def test_hallucinated_date(self):
        ev = _make_ev("Mid-Semester Examination-I is on 15 September 2026.")
        # Hallucinated date 25 December 2026
        answer = "The exam will be held on 25 December 2026."

        validator = GroundingValidator(strict_mode=False)
        res, _ = validator.validate(answer, [ev])

        assert res.is_grounded is False
        assert any("25 December 2026" in e or "2026-12-25" in e for e in res.ungrounded_entities)

    def test_unsupported_regulation(self):
        ev = _make_ev("Course 23CSE302T is offered under Regulation R23.")
        answer = "Course 23CSE302T is offered under Regulation R19."

        validator = GroundingValidator(strict_mode=False)
        res, _ = validator.validate(answer, [ev])

        assert res.is_grounded is False
        assert any("R19" in e for e in res.ungrounded_entities)

    def test_entity_normalization_equivalence(self):
        # 15 September 2026 in evidence, 2026-09-15 in answer
        ev = _make_ev("Examination date is 15 September 2026.")
        answer = "The examination date is 2026-09-15."

        validator = GroundingValidator(strict_mode=False)
        res, _ = validator.validate(answer, [ev])

        assert res.is_grounded is True
        assert res.ungrounded_entities == []

    def test_academic_year_normalization(self):
        ev = _make_ev("The calendar applies to academic year 2026-27.")
        answer = "This schedule is for 2026/27."

        validator = GroundingValidator(strict_mode=False)
        res, _ = validator.validate(answer, [ev])

        assert res.is_grounded is True
        assert res.ungrounded_entities == []

    def test_token_overlap_calculation(self):
        ev = _make_ev("Tree traversals and graph algorithms are essential data structures.")
        answer = "Tree traversals and graph algorithms."

        validator = GroundingValidator(strict_mode=False)
        res, _ = validator.validate(answer, [ev])

        assert res.token_overlap >= 0.8
        assert res.is_grounded is True

    def test_strict_mode_unsafe_remediation_triggers_fallback(self):
        ev = _make_ev("Mid-Semester Examination-I is on 15 September 2026.")
        answer = "All exams are scheduled on 31 December 2099."

        validator = GroundingValidator(strict_mode=True)
        res, final_ans = validator.validate(answer, [ev])

        assert res.is_grounded is False
        assert res.remediation_applied is True
        assert final_ans == INSUFFICIENT_EVIDENCE_FALLBACK

    def test_strict_mode_safe_remediation_removes_unsupported_statement(self):
        ev = _make_ev("Mid-Semester Examination-I is on 15 September 2026.")
        # Statement 1 is grounded; Statement 2 has hallucinated date
        answer = (
            "- Mid-Semester Examination-I is on 15 September 2026.\n"
            "- Final project submission is on 31 December 2099."
        )

        validator = GroundingValidator(strict_mode=True)
        res, final_ans = validator.validate(answer, [ev])

        assert "15 September 2026" in final_ans
        assert "2099" not in final_ans
        assert res.remediation_applied is True

    def test_non_strict_mode_retains_answer_with_diagnostics(self):
        ev = _make_ev("Mid-Semester Examination-I is on 15 September 2026.")
        answer = "Mid-Semester Examination-I is on 20 October 2026."

        validator = GroundingValidator(strict_mode=False)
        res, final_ans = validator.validate(answer, [ev])

        assert res.is_grounded is False
        assert res.remediation_applied is False
        assert final_ans == answer  # Answer is kept in non-strict mode
