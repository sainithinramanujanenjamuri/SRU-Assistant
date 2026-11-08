"""Integration tests for the complete Phase 8 Citation and Provenance RAG Pipeline."""

from generation.grounding.conflict_detector import ConflictDetector
from generation.grounding.validator import GroundingValidator
from generation.llm.deterministic import DeterministicAnswerGenerator
from generation.models import RetrievedEvidence
from generation.pipeline import BaselineRAGPipeline
from generation.prompts.context_builder import ContextBuilder
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK, GroundedPromptTemplate
from retrieval.base import BaseRetriever


class MockCitationRetriever(BaseRetriever):
    """Mock retriever returning predetermined chunks for citation integration tests."""

    def __init__(self, chunks: list[RetrievedEvidence]):
        self.chunks = chunks
        self.retrieval_mode = "enhanced"

    def search(self, query: str, top_k: int = 5, filters=None):
        if "unknown" in query.lower() or "australia" in query.lower():
            return []
        return self.chunks[:top_k]


class TestRAGCitationIntegration:
    """End-to-end integration tests for Citation and Provenance in BaselineRAGPipeline."""

    def _setup_pipeline(self, chunks: list[RetrievedEvidence]):
        retriever = MockCitationRetriever(chunks)
        generator = DeterministicAnswerGenerator()
        context_builder = ContextBuilder(relevance_threshold=0.40)
        prompt_template = GroundedPromptTemplate(style="default")
        conflict_detector = ConflictDetector()
        grounding_validator = GroundingValidator(strict_mode=False)

        return BaselineRAGPipeline(
            retriever=retriever,
            generator=generator,
            context_builder=context_builder,
            prompt_template=prompt_template,
            conflict_detector=conflict_detector,
            grounding_validator=grounding_validator,
        )

    def test_pipeline_produces_citations_and_cited_answer(self) -> None:
        """Verify full grounded query produces structured citations and cited answer."""
        chunks = [
            RetrievedEvidence(
                chunk_id="chunk_cal_01",
                document_id="doc_cal_1",
                document_name="Academic_Calendar_2026_27.pdf",
                page_info="p. 3",
                section_path="Academic Calendar > Examination Schedule",
                text="Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026.",
                score=0.95,
                metadata={"page_number": 3, "section_title": "Examination Schedule"},
            )
        ]
        pipeline = self._setup_pipeline(chunks)
        resp = pipeline.answer_query(
            "When are the mid examinations?",
            citation_style="inline_bracket",
            verify_citations=True,
        )

        assert resp.is_grounded is True
        assert len(resp.citations) == 1
        assert resp.citations[0].citation_id == "1"
        assert resp.citations[0].page == 3
        assert resp.citations[0].page_info == "p. 3"
        assert resp.citations[0].document_name == "Academic_Calendar_2026_27.pdf"
        assert resp.citations[0].is_verified is True

        # Check cited_answer contains [1] and Sources section
        assert resp.cited_answer is not None
        assert "[1]" in resp.cited_answer
        assert "Sources:" in resp.cited_answer

        # Check verification report
        assert resp.citation_verification is not None
        assert resp.citation_verification.is_fully_supported is True
        assert resp.citation_verification.citation_precision == 1.0
        assert resp.citation_verification.citation_recall == 1.0
        assert resp.citation_latency_ms >= 0.0

    def test_pipeline_insufficient_evidence_produces_zero_citations(self) -> None:
        """Verify fallback response produces exactly zero citations and no verification report."""
        pipeline = self._setup_pipeline([])
        resp = pipeline.answer_query("What is the capital of Australia?")

        assert resp.is_grounded is False
        assert resp.answer == INSUFFICIENT_EVIDENCE_FALLBACK
        assert resp.citations == []
        assert resp.citation_verification is None
        assert resp.citation_latency_ms == 0.0

    def test_pipeline_citation_style_switching(self) -> None:
        """Verify switching citation style produces different formatting outputs."""
        chunks = [
            RetrievedEvidence(
                chunk_id="chunk_cal_01",
                document_id="doc_cal_1",
                document_name="Academic_Calendar_2026_27.pdf",
                page_info="p. 3",
                section_path="Examination Schedule",
                text="Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026.",
                score=0.95,
                metadata={"page_number": 3},
            )
        ]
        pipeline = self._setup_pipeline(chunks)

        # Style 1: source_block
        resp_block = pipeline.answer_query(
            "When are the mid examinations?",
            citation_style="source_block",
        )
        assert resp_block.cited_answer is not None
        assert "Source:" in resp_block.cited_answer or "Sources:" in resp_block.cited_answer
        assert "[1]" not in resp_block.cited_answer

        # Style 2: footnote
        resp_fn = pipeline.answer_query(
            "When are the mid examinations?",
            citation_style="footnote",
        )
        assert resp_fn.cited_answer is not None
        assert "Footnotes:" in resp_fn.cited_answer
        assert "¹" in resp_fn.cited_answer

    def test_pipeline_multiple_source_answer(self) -> None:
        """Verify query synthesized across multiple documents produces distinct source citations."""
        chunks = [
            RetrievedEvidence(
                chunk_id="chunk_syl_1",
                document_id="doc_syl_1",
                document_name="Syllabus_23CSE302T.pdf",
                page_info="p. 1",
                section_path="Objectives",
                text="Course 23CSE302T: Advanced Data Structures covers tree traversals and graph algorithms.",
                score=0.90,
                metadata={"page_number": 1},
            ),
            RetrievedEvidence(
                chunk_id="chunk_cal_1",
                document_id="doc_cal_1",
                document_name="Academic_Calendar_2026_27.pdf",
                page_info="p. 3",
                section_path="Examination Schedule",
                text="Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026.",
                score=0.88,
                metadata={"page_number": 3},
            ),
        ]
        pipeline = self._setup_pipeline(chunks)
        resp = pipeline.answer_query("What is 23CSE302T and when is the mid examination?")

        assert resp.is_grounded is True
        assert len(resp.citations) >= 2
        cit_docs = {c.document_name for c in resp.citations}
        assert "Syllabus_23CSE302T.pdf" in cit_docs
        assert "Academic_Calendar_2026_27.pdf" in cit_docs

    def test_pipeline_missing_provenance_never_fabricates_pages(self) -> None:
        """Verify chunks with missing page numbers output p. N/A and page=None."""
        chunks = [
            RetrievedEvidence(
                chunk_id="chunk_circ_1",
                document_id="doc_circ_1",
                document_name="Circular.pdf",
                page_info="p. N/A",
                section_path="N/A",
                text="Students must register for courses before 30 July 2026.",
                score=0.85,
                metadata={},  # No page_number metadata
            )
        ]
        pipeline = self._setup_pipeline(chunks)
        resp = pipeline.answer_query("When is course registration deadline?")

        if resp.citations:
            assert resp.citations[0].page is None
            assert resp.citations[0].page_info == "p. N/A"
            assert "p. N/A" in resp.citations[0].source
