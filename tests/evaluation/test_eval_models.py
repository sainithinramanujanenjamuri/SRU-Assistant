"""Unit tests for Phase 9 evaluation models."""

import pytest
from pydantic import ValidationError

from evaluation.models import (
    CANONICAL_BENCHMARK_CATEGORIES,
    BenchmarkQuery,
    CitationMetrics,
    EvaluationReport,
    ExperimentRunResult,
    GenerationMetrics,
    LatencyBreakdown,
    QueryEvaluationResult,
    RetrievalMetrics,
)


def test_benchmark_query_valid():
    """Test valid BenchmarkQuery construction."""
    q = BenchmarkQuery(
        query_id="q_test_01",
        query="When is the exam?",
        category="date_based",
        expected_answer="12 September 2026",
        expected_chunk_ids=["chunk_1"],
        expected_document_names=["calendar.txt"],
        expected_pages=[None],
        expected_entities=["12 September 2026"],
        expected_behavior="answer",
        is_answerable=True,
    )
    assert q.query_id == "q_test_01"
    assert q.category == "date_based"
    assert q.is_answerable is True


def test_benchmark_query_invalid_category():
    """Test that non-canonical categories raise a validation error."""
    with pytest.raises(ValidationError, match="Unknown benchmark category"):
        BenchmarkQuery(
            query_id="q_bad",
            query="Some query",
            category="unsupported_category_name",
            expected_answer="Some answer",
        )


def test_benchmark_query_immutability():
    """Test that BenchmarkQuery is frozen."""
    q = BenchmarkQuery(
        query_id="q_test_frozen",
        query="Some query",
        category="direct_factual",
        expected_answer="Some answer",
    )
    with pytest.raises(ValidationError):
        q.category = "date_based"  # type: ignore[misc]


def test_retrieval_metrics_validation():
    """Test RetrievalMetrics bounds validation."""
    m = RetrievalMetrics(
        recall_at_k={1: 0.5, 5: 1.0},
        precision_at_k={1: 1.0, 5: 0.4},
        mrr=0.5,
        ndcg_at_k={5: 0.85},
    )
    assert m.mrr == 0.5

    with pytest.raises(ValidationError):
        RetrievalMetrics(mrr=1.5)

    with pytest.raises(ValidationError):
        RetrievalMetrics(mrr=-0.2)


def test_generation_metrics_validation():
    """Test GenerationMetrics bounds validation."""
    gm = GenerationMetrics(
        groundedness=0.9,
        answer_relevance=0.8,
        context_relevance=0.7,
        correctness=0.85,
        completeness=1.0,
        unsupported_claim_rate=0.1,
    )
    assert gm.groundedness == 0.9

    with pytest.raises(ValidationError):
        GenerationMetrics(groundedness=1.2)


def test_citation_metrics_validation():
    """Test CitationMetrics bounds validation."""
    cm = CitationMetrics(
        citation_precision=1.0,
        citation_recall=0.8,
        citation_completeness=0.8,
        evidence_support=0.95,
    )
    assert cm.citation_precision == 1.0

    with pytest.raises(ValidationError):
        CitationMetrics(citation_precision=-0.1)


def test_canonical_categories_count():
    """Verify exactly 10 canonical benchmark categories from roadmap.md."""
    assert len(CANONICAL_BENCHMARK_CATEGORIES) == 10
    expected = {
        "direct_factual",
        "date_based",
        "course_related",
        "regulation",
        "department_specific",
        "multi_document",
        "paraphrased",
        "ambiguous",
        "out_of_knowledge_base",
        "version_sensitive",
    }
    assert set(CANONICAL_BENCHMARK_CATEGORIES) == expected
