"""End-to-end integration tests for the Phase 4 Baseline RAG pipeline."""

import pytest

from generation.llm.deterministic import DeterministicAnswerGenerator
from generation.pipeline import BaselineRAGPipeline
from generation.prompts.context_builder import ContextBuilder
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK
from ingestion.chunking.structure_aware import StructureAwareChunker
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.vectorstore.indexer import VectorIndexer
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore
from tests.fixtures.synthetic_processed_docs import (
    create_fixture_academic_calendar,
    create_fixture_normal_syllabus,
    create_fixture_with_small_table,
)


@pytest.fixture
def integrated_rag_pipeline(tmp_path):
    """Set up complete end-to-end pipeline from document chunks to RAG response."""
    db_path = str(tmp_path / "rag_test_vectors.db")
    store = SQLiteVectorStore(db_path=db_path)
    model = FastHashEmbeddingModel(dimension=384)
    indexer = VectorIndexer(embedding_model=model, vector_store=store)
    chunker = StructureAwareChunker(target_tokens=300, overlap_tokens=50)

    docs = [
        create_fixture_normal_syllabus("doc_syllabus"),
        create_fixture_academic_calendar("doc_calendar"),
        create_fixture_with_small_table("doc_courses"),
    ]

    all_chunks = []
    for doc in docs:
        all_chunks.extend(chunker.chunk_document(doc))

    indexer.index_chunks(all_chunks)

    retriever = VectorRetriever(embedding_model=model, vector_store=store)
    generator = DeterministicAnswerGenerator()
    context_builder = ContextBuilder(relevance_threshold=0.40)

    return BaselineRAGPipeline(
        retriever=retriever,
        generator=generator,
        context_builder=context_builder,
    )


class TestBaselineRAGIntegration:
    """End-to-end testing of baseline RAG query answering, attribution, and fallback."""

    def test_exam_schedule_query_grounded_answer(self, integrated_rag_pipeline):
        query = "When do the mid-semester examinations start for B.Tech?"
        response = integrated_rag_pipeline.answer_query(query=query, top_k=3)

        assert response.query == query
        assert response.is_grounded is True
        assert response.is_llm is False
        assert "12 September 2026" in response.answer

        # Source attribution checks
        assert len(response.evidence) > 0
        top_evidence = response.evidence[0]
        assert top_evidence.document_id == "doc_calendar"
        assert top_evidence.score >= 0.40

        # Latency breakdown checks
        assert response.retrieval_latency_ms >= 0.0
        assert response.context_latency_ms >= 0.0
        assert response.generation_latency_ms >= 0.0
        assert response.total_latency_ms >= response.retrieval_latency_ms

    def test_syllabus_query_grounded_answer(self, integrated_rag_pipeline):
        query = "What tree traversals and graph algorithms are covered in course 23CSE302T?"
        response = integrated_rag_pipeline.answer_query(query=query, top_k=3)

        assert response.is_grounded is True
        assert "tree traversals" in response.answer.lower() or "algorithms" in response.answer.lower()
        assert any(ev.document_id == "doc_syllabus" for ev in response.evidence)

    def test_insufficient_evidence_fallback_and_no_generator_call(self, integrated_rag_pipeline):
        # Query with non-matching filter produces 0 evidence chunks
        query = "What are the rules and timings for the university swimming pool?"
        response = integrated_rag_pipeline.answer_query(
            query=query, top_k=3, filters={"department": "NonExistentDept"}
        )

        assert response.answer == INSUFFICIENT_EVIDENCE_FALLBACK
        assert response.is_grounded is False
        assert response.evidence == []
        # Generator must NOT be called when no evidence survives
        assert response.generation_latency_ms == 0.0

    def test_unrelated_query_with_low_relevance_fallback(self, integrated_rag_pipeline):
        # Query about topics completely unrelated to syllabus and calendar
        query = "What are the guidelines for Olympic swimming pool construction?"
        response = integrated_rag_pipeline.answer_query(query=query, top_k=3)

        assert response.answer == INSUFFICIENT_EVIDENCE_FALLBACK
        assert response.is_grounded is False

    def test_empty_query_raises_value_error(self, integrated_rag_pipeline):
        with pytest.raises(ValueError, match="Query string cannot be empty"):
            integrated_rag_pipeline.answer_query(query="")

    def test_invalid_top_k_raises_value_error(self, integrated_rag_pipeline):
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            integrated_rag_pipeline.answer_query(query="exams", top_k=0)
