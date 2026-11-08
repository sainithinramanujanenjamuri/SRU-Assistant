"""Unit tests for EnhancedRetriever coordinator."""
from __future__ import annotations


import pytest

from retrieval.base import BaseRetriever
from retrieval.enhanced_retriever import EnhancedRetriever
from retrieval.filtering.metadata_filter import MetadataFilter
from retrieval.models import HybridSearchResult, RerankerUnavailableError, RerankResult
from retrieval.query.analyzer import AcademicQueryAnalyzer
from retrieval.reranking.base import BaseReranker
from retrieval.reranking.deterministic import DeterministicCrossFeatureReranker
from retrieval.reranking.passthrough import PassthroughReranker


class MockHybridRetriever(BaseRetriever):
    """Mock HybridRetriever returning fixed synthetic candidates for deterministic testing."""


    def __init__(self, candidates: list[HybridSearchResult]):
        self.candidates = candidates
        self.last_query = None
        self.last_top_k = None
        self.last_filters = None

    def search(self, query: str, top_k: int = 5, filters: dict | None = None) -> list[HybridSearchResult]:
        self.last_query = query
        self.last_top_k = top_k
        self.last_filters = filters
        return list(self.candidates[:top_k])


class FailingReranker(BaseReranker):
    reranker_name = "failing"
    reranker_provider = "test"
    reranker_model = "fail-v1"

    def rerank(self, query: str, candidates: list, top_k: int = 5) -> list[RerankResult]:
        raise RerankerUnavailableError("Simulated neural reranker failure.")


@pytest.fixture
def sample_candidates() -> list[HybridSearchResult]:
    return [
        HybridSearchResult(
            chunk_id="chunk_cal",
            document_id="doc_calendar",
            text="Academic Calendar 2026-27. Mid examinations start 12 September 2026.",
            fused_score=0.85,
            normalized_fused_score=0.85,
            metadata={"department": None, "academic_year": "2026-27"},
            provenance={"source_file": "calendar.txt"},
        ),
        HybridSearchResult(
            chunk_id="chunk_cse",
            document_id="doc_syllabus",
            text="Course 23CSE302T Data Structures and Algorithms for CSE students.",
            fused_score=0.75,
            normalized_fused_score=0.75,
            metadata={"department": "Computer Science and Engineering", "semester": "Semester VII"},
            provenance={"source_file": "syllabus.pdf"},
        ),
        HybridSearchResult(
            chunk_id="chunk_ece",
            document_id="doc_ece",
            text="Digital Signal Processing for ECE department.",
            fused_score=0.70,
            normalized_fused_score=0.70,
            metadata={"department": "Electronics and Communication Engineering"},
            provenance={"source_file": "ece.pdf"},
        ),
    ]


def test_enhanced_retriever_full_pipeline(sample_candidates: list[HybridSearchResult]):
    mock_hybrid = MockHybridRetriever(sample_candidates)
    enhanced = EnhancedRetriever(
        hybrid_retriever=mock_hybrid,
        reranker=DeterministicCrossFeatureReranker(),
        query_analyzer=AcademicQueryAnalyzer(),
        metadata_filter=MetadataFilter(mode="soft"),
        candidate_k=20,
        filter_mode="soft",
        enable_query_analysis=True,
        enable_reranking=True,
    )

    results = enhanced.search(query="When are the mid exams in the calendar?", top_k=2)

    assert len(results) == 2
    assert results[0].chunk_id == "chunk_cal"
    assert enhanced.last_meta is not None
    meta = enhanced.last_meta
    assert meta.initial_candidate_count == 3
    assert meta.post_filter_count == 3
    assert meta.final_count == 2
    assert meta.reranker_name == "deterministic"
    assert meta.total_retrieval_latency_ms >= 0.0


def test_enhanced_retriever_hard_filter_pruning(sample_candidates: list[HybridSearchResult]):
    mock_hybrid = MockHybridRetriever(sample_candidates)
    enhanced = EnhancedRetriever(
        hybrid_retriever=mock_hybrid,
        reranker=PassthroughReranker(),
        filter_mode="hard",
    )

    # When querying for CSE, ECE document should be excluded, calendar should be preserved
    results = enhanced.search(
        query="Syllabus",
        top_k=5,
        filters={"department": "CSE"},
    )
    result_ids = [r.chunk_id for r in results]
    assert "chunk_cal" in result_ids, "Global calendar must survive hard filter"
    assert "chunk_cse" in result_ids, "Matching CSE document must survive"
    assert "chunk_ece" not in result_ids, "Mismatching ECE document must be pruned"


def test_enhanced_retriever_empty_candidates():
    mock_hybrid = MockHybridRetriever([])
    enhanced = EnhancedRetriever(hybrid_retriever=mock_hybrid)

    results = enhanced.search(query="Any query", top_k=5)
    assert results == []
    assert enhanced.last_meta is not None
    assert enhanced.last_meta.initial_candidate_count == 0
    assert enhanced.last_meta.final_count == 0


def test_enhanced_retriever_reranker_failure_without_fallback(sample_candidates: list[HybridSearchResult]):
    mock_hybrid = MockHybridRetriever(sample_candidates)
    enhanced = EnhancedRetriever(
        hybrid_retriever=mock_hybrid,
        reranker=FailingReranker(),
        allow_reranker_fallback=False,
    )

    with pytest.raises(RerankerUnavailableError):
        enhanced.search(query="Test query", top_k=2)


def test_enhanced_retriever_reranker_failure_with_fallback(sample_candidates: list[HybridSearchResult]):
    mock_hybrid = MockHybridRetriever(sample_candidates)
    enhanced = EnhancedRetriever(
        hybrid_retriever=mock_hybrid,
        reranker=FailingReranker(),
        allow_reranker_fallback=True,  # Explicit fallback enabled
    )

    results = enhanced.search(query="Test query", top_k=2)
    assert len(results) == 2
    assert enhanced.last_meta is not None
    # Model should reflect that fallback occurred
    assert enhanced.last_meta.reranker_name == "deterministic"
