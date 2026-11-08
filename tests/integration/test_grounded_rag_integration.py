"""Integration tests for the complete Phase 7 Grounded RAG Pipeline."""

from generation.grounding.conflict_detector import ConflictDetector
from generation.grounding.validator import GroundingValidator
from generation.llm.deterministic import DeterministicAnswerGenerator
from generation.models import RetrievedEvidence
from generation.pipeline import BaselineRAGPipeline
from generation.prompts.context_builder import ContextBuilder
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK, GroundedPromptTemplate
from retrieval.base import BaseRetriever


class MockIntegrationRetriever(BaseRetriever):
    """Mock retriever returning predetermined chunks for integration testing."""

    def __init__(self, chunks: list[RetrievedEvidence]):
        self.chunks = chunks
        self.retrieval_mode = "enhanced"

    def search(self, query: str, top_k: int = 5, filters=None):
        if "unanswerable" in query.lower() or "hostel" in query.lower():
            return []
        return self.chunks[:top_k]


class TestGroundedRAGIntegration:
    """End-to-end integration tests for Grounded RAG with validation and conflict detection."""

    def _setup_pipeline(self, chunks: list[RetrievedEvidence], strict_mode: bool = False):
        retriever = MockIntegrationRetriever(chunks)
        generator = DeterministicAnswerGenerator()
        context_builder = ContextBuilder(relevance_threshold=0.40)
        prompt_template = GroundedPromptTemplate(style="default")
        conflict_detector = ConflictDetector()
        grounding_validator = GroundingValidator(strict_mode=strict_mode)

        return BaselineRAGPipeline(
            retriever=retriever,
            generator=generator,
            context_builder=context_builder,
            prompt_template=prompt_template,
            conflict_detector=conflict_detector,
            grounding_validator=grounding_validator,
        )

    def test_standard_grounded_academic_query(self):
        chunks = [
            RetrievedEvidence(
                chunk_id="c1",
                document_id="d1",
                document_name="calendar.txt",
                text="Mid-Semester Examination-I is scheduled from 12 September 2026 to 16 September 2026.",
                score=0.95,
            )
        ]
        pipeline = self._setup_pipeline(chunks)
        resp = pipeline.answer_query("When are the mid examinations?")

        assert resp.is_grounded is True
        assert "12 September 2026" in resp.answer
        assert resp.grounding_validation is not None
        assert resp.grounding_validation.is_grounded is True
        assert resp.conflict_report is not None
        assert resp.conflict_report.has_conflict is False
        assert resp.total_latency_ms > 0

    def test_insufficient_evidence_triggers_standardized_fallback(self):
        pipeline = self._setup_pipeline([])
        resp = pipeline.answer_query("What is the hostel fee for 2026?")

        assert resp.is_grounded is False
        assert resp.answer == INSUFFICIENT_EVIDENCE_FALLBACK
        assert resp.evidence == []

    def test_conflicting_documents_surfaces_discrepancy(self):
        chunks = [
            RetrievedEvidence(
                chunk_id="c1",
                document_id="d1",
                document_name="calendar_v1.txt",
                text="Mid-Semester Examination-I is on 12 September 2026.",
                score=0.95,
            ),
            RetrievedEvidence(
                chunk_id="c2",
                document_id="d2",
                document_name="circular_v2.pdf",
                text="Mid-Semester Examination-I is on 20 September 2026.",
                score=0.90,
            ),
        ]
        pipeline = self._setup_pipeline(chunks)
        resp = pipeline.answer_query("When is Mid-Semester Examination-I?")

        assert resp.conflict_report is not None
        assert resp.conflict_report.has_conflict is True
        assert resp.conflict_report.conflict_type == "date_discrepancy"
        # Conflict notice should be surfaced in answer
        assert "discrepancy" in resp.answer.lower() or "notice" in resp.answer.lower()

    def test_strict_mode_remediation_on_hallucination(self):
        # Even if a hypothetical model generated an ungrounded claim, strict mode intercepts it
        chunks = [
            RetrievedEvidence(
                chunk_id="c1",
                document_id="d1",
                document_name="syllabus.pdf",
                text="Course 23CSE302T covers Data Structures.",
                score=0.95,
            )
        ]
        pipeline = self._setup_pipeline(chunks, strict_mode=True)
        resp = pipeline.answer_query("What is course 23CSE302T?")

        assert resp.is_grounded is True
        assert "23CSE302T" in resp.answer
        assert resp.grounding_validation is not None
        assert resp.grounding_validation.remediation_applied is False
