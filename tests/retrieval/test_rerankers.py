"""Unit tests for Re-ranker subsystem (deterministic baseline, adapters, factory)."""
from __future__ import annotations


import pytest

from retrieval.models import HybridSearchResult, RerankerUnavailableError
from retrieval.reranking import (
    DeterministicCrossEncoderReranker,
    DeterministicCrossFeatureReranker,
    OllamaCrossEncoderReranker,
    PassthroughReranker,
    TransformerCrossEncoderReranker,
    get_reranker,
)


def make_cand(chunk_id: str, text: str, score: float = 0.5, meta: dict | None = None) -> HybridSearchResult:
    return HybridSearchResult(
        chunk_id=chunk_id,
        document_id="doc_" + chunk_id,
        text=text,
        fused_score=score,
        normalized_fused_score=score,
        metadata=meta or {},
        provenance={"source_file": "test.txt"},
    )


def test_deterministic_reranker_exact_entity_match():
    reranker = DeterministicCrossFeatureReranker()
    cands = [
        make_cand("c1", "General description of algorithms and programming concepts."),
        make_cand("c2", "Syllabus and learning outcomes for course 23CSE302T."),
    ]
    results = reranker.rerank(query="What is covered in 23CSE302T?", candidates=cands, top_k=2)

    assert len(results) == 2
    # c2 contains the exact course code, so it must rank #1
    assert results[0].chunk_id == "c2"
    assert results[0].rerank_rank == 1
    assert results[0].rerank_score > results[1].rerank_score
    assert results[0].reranker_name == "deterministic"
    assert results[0].reranker_provider == "deterministic"


def test_deterministic_reranker_date_match():
    reranker = DeterministicCrossFeatureReranker()
    cands = [
        make_cand("c_irrelevant", "General university rules and campus regulations."),
        make_cand(
            "c_calendar",
            "Academic Calendar 2026-27. First Mid Examinations: 12 September 2026 to 16 September 2026.",
            meta={"chunk_dates": ["12 September 2026"]},
        ),
    ]
    results = reranker.rerank(
        query="When are the mid exams on 12 September 2026?",
        candidates=cands,
        top_k=2,
    )
    assert results[0].chunk_id == "c_calendar"
    assert results[0].rerank_score > results[1].rerank_score
    assert results[0].rerank_score >= 0.45


def test_deterministic_reranker_rank_movement_and_delta():
    reranker = DeterministicCrossFeatureReranker()
    # c1 is initial rank 1 (score 0.8), but c2 has exact course code match
    c1 = make_cand("c1", "General algorithms introduction.", score=0.8)
    c2 = make_cand("c2", "Course 23CSE302T covers trees and graph structures.", score=0.3)

    results = reranker.rerank(query="Course 23CSE302T", candidates=[c1, c2], top_k=2)

    # c2 should be promoted to rank 1
    assert results[0].chunk_id == "c2"
    assert results[0].initial_rank == 2
    assert results[0].rerank_rank == 1
    # rank_delta = initial_rank - rerank_rank = 2 - 1 = +1 (promoted)
    assert results[0].rank_delta == 1

    # c1 should be demoted to rank 2
    assert results[1].chunk_id == "c1"
    assert results[1].initial_rank == 1
    assert results[1].rerank_rank == 2
    # rank_delta = 1 - 2 = -1 (demoted)
    assert results[1].rank_delta == -1


def test_deterministic_tie_breaking():
    reranker = DeterministicCrossFeatureReranker()
    # Two identical candidates with identical scores: chunk_id ASC must break tie
    c_beta = make_cand("chunk_b", "Identical content for testing tie breaking.")
    c_alpha = make_cand("chunk_a", "Identical content for testing tie breaking.")

    results = reranker.rerank(query="Identical content", candidates=[c_beta, c_alpha], top_k=2)
    assert results[0].chunk_id == "chunk_a"
    assert results[1].chunk_id == "chunk_b"


def test_deterministic_reranker_score_bounds():
    reranker = DeterministicCrossFeatureReranker()
    cands = [
        make_cand("c1", "Completely unrelated words here xyz abc"),
        make_cand("c2", "Syllabus 23CSE302T under R23 on 12 September 2026 First Mid Examinations"),
    ]
    results = reranker.rerank(query="23CSE302T R23 12 September 2026", candidates=cands, top_k=2)
    for r in results:
        assert 0.0 <= r.rerank_score <= 1.0


def test_empty_candidates_returns_empty():
    reranker = DeterministicCrossFeatureReranker()
    assert reranker.rerank("Query", candidates=[], top_k=5) == []


def test_invalid_arguments_raise_value_error():
    reranker = DeterministicCrossFeatureReranker()
    with pytest.raises(ValueError):
        reranker.rerank("", candidates=[], top_k=5)
    with pytest.raises(ValueError):
        reranker.rerank("Valid query", candidates=[], top_k=0)
    with pytest.raises(ValueError):
        reranker.rerank("Valid query", candidates=[], top_k=-1)


def test_passthrough_reranker():
    passthrough = PassthroughReranker()
    c1 = make_cand("c1", "Text 1", score=0.9)
    c2 = make_cand("c2", "Text 2", score=0.7)

    results = passthrough.rerank(query="Any query", candidates=[c1, c2], top_k=2)
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[0].rerank_score == 0.9
    assert results[0].rank_delta == 0
    assert results[0].reranker_name == "passthrough"
    assert results[0].reranker_provider == "passthrough"
    assert results[0].reranker_model == "identity"


def test_transformer_reranker_unavailable_raises_error():
    """If sentence-transformers is not available, must raise RerankerUnavailableError without silent fallback."""

    reranker = TransformerCrossEncoderReranker(model_name="nonexistent-model-or-missing-pkg")
    cands = [make_cand("c1", "Some text")]

    with pytest.raises(RerankerUnavailableError):
        reranker.rerank(query="Query", candidates=cands, top_k=1)


def test_ollama_reranker_unavailable_raises_error():
    """If Ollama is unreachable at invalid port, must raise RerankerUnavailableError without silent fallback."""
    reranker = OllamaCrossEncoderReranker(api_base="http://localhost:59999", timeout_seconds=1.0)
    cands = [make_cand("c1", "Some text")]

    with pytest.raises(RerankerUnavailableError):
        reranker.rerank(query="Query", candidates=cands, top_k=1)


def test_reranker_factory():
    det = get_reranker("deterministic")
    assert isinstance(det, DeterministicCrossFeatureReranker)
    assert isinstance(det, DeterministicCrossEncoderReranker)

    pt = get_reranker("passthrough")
    assert isinstance(pt, PassthroughReranker)

    tf = get_reranker("transformer")
    assert isinstance(tf, TransformerCrossEncoderReranker)

    ol = get_reranker("ollama")
    assert isinstance(ol, OllamaCrossEncoderReranker)

    with pytest.raises(ValueError):
        get_reranker("unsupported_reranker_type")
