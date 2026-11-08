"""Integration tests connecting EnhancedRetriever to BaselineRAGPipeline (Phase 6)."""

import pytest

from app.config.settings import get_settings
from generation.llm.deterministic import DeterministicAnswerGenerator
from generation.pipeline import BaselineRAGPipeline
from generation.prompts.context_builder import ContextBuilder
from retrieval.embeddings.factory import get_embedding_model
from retrieval.enhanced_retriever import EnhancedRetriever
from retrieval.fusion.hybrid import HybridRetriever
from retrieval.lexical.bm25 import BM25Retriever
from retrieval.reranking.deterministic import DeterministicCrossFeatureReranker
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


@pytest.fixture
def enhanced_pipeline():
    settings = get_settings()
    embedding_model = get_embedding_model()
    vector_store = SQLiteVectorStore(db_path=settings.vectorstore_path)
    dense_retriever = VectorRetriever(embedding_model=embedding_model, vector_store=vector_store)

    lexical_retriever = BM25Retriever.from_file(index_path=settings.bm25_index_path)

    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        lexical_retriever=lexical_retriever,
        fusion_method="rrf",
        dense_candidate_k=20,
        lexical_candidate_k=20,
    )

    enhanced_retriever = EnhancedRetriever(
        hybrid_retriever=hybrid_retriever,
        reranker=DeterministicCrossFeatureReranker(),
        filter_mode="soft",
        enable_query_analysis=True,
        enable_reranking=True,
    )

    generator = DeterministicAnswerGenerator()
    context_builder = ContextBuilder(relevance_threshold=0.20)

    return BaselineRAGPipeline(
        retriever=enhanced_retriever,
        generator=generator,
        context_builder=context_builder,
    )


def test_enhanced_rag_pipeline_end_to_end(enhanced_pipeline: BaselineRAGPipeline):
    """Verify end-to-end question answering with EnhancedRetriever."""
    query = "When are the mid examinations scheduled?"
    response = enhanced_pipeline.answer_query(query=query, top_k=3)

    assert response.is_grounded is True
    assert "examination" in response.answer.lower()
    assert len(response.evidence) > 0

    # Verify reranking metadata is preserved on evidence items
    top_ev = response.evidence[0]
    assert top_ev.rerank_score is not None
    assert top_ev.reranker_name == "deterministic"
    assert top_ev.initial_rank is not None
    assert top_ev.rerank_rank is not None

    # Verify enhanced_meta is captured on RAGResponse
    assert response.enhanced_meta is not None
    assert response.enhanced_meta["reranker_name"] == "deterministic"
    assert response.enhanced_meta["total_retrieval_latency_ms"] >= 0.0


def test_enhanced_rag_no_evidence_fallback(enhanced_pipeline: BaselineRAGPipeline):
    """Unanswerable query with high threshold triggers safe institutional fallback."""
    # Set high relevance threshold so zero chunks survive
    enhanced_pipeline.context_builder.threshold = 0.99
    response = enhanced_pipeline.answer_query(query="Quantum string entanglement in astrophysics", top_k=3)

    assert response.is_grounded is False
    assert "couldn't find sufficient information" in response.answer
    assert response.evidence == []


def test_phase4_compatibility_regression():
    """Verify that BaselineRAGPipeline still functions cleanly with standard VectorRetriever."""
    settings = get_settings()
    embedding_model = get_embedding_model()
    vector_store = SQLiteVectorStore(db_path=settings.vectorstore_path)
    dense_retriever = VectorRetriever(embedding_model=embedding_model, vector_store=vector_store)
    generator = DeterministicAnswerGenerator()
    pipeline = BaselineRAGPipeline(retriever=dense_retriever, generator=generator)

    response = pipeline.answer_query(query="When are the mid examinations scheduled?", top_k=2)
    assert response.is_grounded is True
    assert len(response.evidence) > 0
    assert response.retrieval_mode == "dense"
