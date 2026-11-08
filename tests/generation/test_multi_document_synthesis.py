"""Unit tests for multi-document synthesis and entity preservation."""

from generation.llm.deterministic import DeterministicAnswerGenerator
from generation.models import RetrievedEvidence
from generation.prompts.context_builder import ContextBuilder
from generation.prompts.templates import GroundedPromptTemplate


class TestMultiDocumentSynthesis:
    """Test suite for combining evidence across distinct academic documents."""

    def test_syllabus_and_calendar_synthesis(self):
        ev1 = RetrievedEvidence(
            chunk_id="c_syl",
            document_id="doc_syl",
            document_name="syllabus_23cse302t.pdf",
            section_path="Course Overview",
            page_info="p. 1",
            text="Course 23CSE302T covers Advanced Data Structures, tree traversals, and graph algorithms.",
            score=0.92,
        )
        ev2 = RetrievedEvidence(
            chunk_id="c_cal",
            document_id="doc_cal",
            document_name="calendar_2026_27.txt",
            section_path="Examination Schedule",
            page_info="p. 1",
            text="Mid-Semester Examination-I is scheduled from 12 September 2026 to 16 September 2026.",
            score=0.90,
        )

        builder = ContextBuilder(relevance_threshold=0.40)
        ctx = builder.build_context(
            query="What is 23CSE302T and when is the mid examination?",
            search_results=[ev1, ev2],
        )

        assert len(ctx.evidence_items) == 2
        assert "[Source 1]" in ctx.formatted_context_text
        assert "[Source 2]" in ctx.formatted_context_text

        tmpl = GroundedPromptTemplate()
        prompt = tmpl.render_full_prompt(ctx)

        generator = DeterministicAnswerGenerator()
        resp = generator.generate(prompt)

        # Verified synthesized answer includes facts from both documents
        assert "23CSE302T" in resp.text
        assert "12 September 2026" in resp.text
        assert "tree traversals" in resp.text

    def test_preservation_of_exact_course_code_and_regulation(self):
        ev = RetrievedEvidence(
            chunk_id="c1",
            document_id="d1",
            document_name="curriculum.pdf",
            text="Course 23CSE302T is offered in Semester VII under Academic Regulation R23.",
            score=0.95,
        )
        builder = ContextBuilder(relevance_threshold=0.40)
        ctx = builder.build_context(query="What regulation applies to 23CSE302T?", search_results=[ev])

        tmpl = GroundedPromptTemplate()
        prompt = tmpl.render_full_prompt(ctx)

        generator = DeterministicAnswerGenerator()
        resp = generator.generate(prompt)

        assert "23CSE302T" in resp.text
        assert "R23" in resp.text
        assert "Semester VII" in resp.text

    def test_no_manufactured_relationships(self):
        # Query asks about course 23CSE302T
        # Evidence has 23CSE302T, but date is for unrelated mechanical course
        ev1 = RetrievedEvidence(
            chunk_id="c1",
            document_id="d1",
            document_name="cse.pdf",
            text="Course 23CSE302T is a Computer Science course.",
            score=0.9,
        )
        ev2 = RetrievedEvidence(
            chunk_id="c2",
            document_id="d2",
            document_name="mech.pdf",
            text="Mechanical engineering diploma practical exam is on 01 October 2026.",
            score=0.5,
        )

        builder = ContextBuilder(relevance_threshold=0.40)
        ctx = builder.build_context(query="Tell me about 23CSE302T", search_results=[ev1, ev2])

        tmpl = GroundedPromptTemplate()
        prompt = tmpl.render_full_prompt(ctx)

        generator = DeterministicAnswerGenerator()
        resp = generator.generate(prompt)

        assert "23CSE302T" in resp.text
        assert "Mechanical" not in resp.text
