"""Unit tests for generation quality, RAG Triad, and citation metrics."""

import pytest

from citations.models import ClaimItem
from evaluation.generation.metrics import (
    compute_answer_relevance,
    compute_completeness,
    compute_context_relevance,
    compute_correctness,
    compute_groundedness,
    compute_unsupported_claim_rate,
)
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK


def test_compute_groundedness():
    """Test groundedness calculation across claim support states."""
    # 1. All claims supported
    claims_supported = [
        ClaimItem(claim_id="c1", claim_text="Fact 1", claim_type="factual", is_supported=True),
        ClaimItem(claim_id="c2", claim_text="Fact 2", claim_type="factual", is_supported=True),
    ]
    assert compute_groundedness(claims_supported, "Answer", is_fallback=False) == 1.0

    # 2. Mixed support
    claims_mixed = [
        ClaimItem(claim_id="c1", claim_text="Fact 1", claim_type="factual", is_supported=True),
        ClaimItem(claim_id="c2", claim_text="Fact 2", claim_type="factual", is_supported=False),
    ]
    assert compute_groundedness(claims_mixed, "Answer", is_fallback=False) == 0.5

    # 3. None supported
    claims_none = [
        ClaimItem(claim_id="c1", claim_text="Fact 1", claim_type="factual", is_supported=False),
    ]
    assert compute_groundedness(claims_none, "Answer", is_fallback=False) == 0.0

    # 4. Fallback is always grounded (no hallucinated claims)
    assert compute_groundedness([], INSUFFICIENT_EVIDENCE_FALLBACK, is_fallback=True) == 1.0


def test_compute_answer_relevance():
    """Test answer relevance for answerable and unanswerable queries."""
    query = "When is the Mid-Semester Examination?"
    answer = "Mid-Semester Examination is scheduled on 12 September 2026."

    # In-KB answerable with good answer
    score = compute_answer_relevance(query, answer, is_answerable=True, is_fallback=False)
    assert score > 0.5

    # In-KB answerable yielding fallback (missed answer)
    assert compute_answer_relevance(query, INSUFFICIENT_EVIDENCE_FALLBACK, is_answerable=True, is_fallback=True) == 0.0

    # Out-of-KB unanswerable query yielding fallback (correct behavior)
    assert compute_answer_relevance(query, INSUFFICIENT_EVIDENCE_FALLBACK, is_answerable=False, is_fallback=True) == 1.0

    # Out-of-KB unanswerable query yielding hallucinated answer (incorrect behavior)
    assert compute_answer_relevance(query, answer, is_answerable=False, is_fallback=False) == 0.0


def test_compute_context_relevance():
    """Test context relevance calculation."""
    retrieved = ["c1", "c2", "c3"]
    expected = ["c1", "c2"]
    score = compute_context_relevance(retrieved, expected)
    assert pytest.approx(score, 0.001) == 2.0 / 3.0

    # Empty retrieved
    assert compute_context_relevance([], ["c1"]) == 0.0
    assert compute_context_relevance([], []) == 1.0


def test_compute_correctness():
    """Test token F1 correctness calculation."""
    gold = "Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026."
    actual = "Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026."
    assert compute_correctness(actual, gold, is_answerable=True, is_fallback=False) == 1.0

    # Partial overlap
    partial = "Mid-Semester Examination I is in September."
    score = compute_correctness(partial, gold, is_answerable=True, is_fallback=False)
    assert 0.0 < score < 1.0

    # Fallback on answerable query
    assert compute_correctness(INSUFFICIENT_EVIDENCE_FALLBACK, gold, is_answerable=True, is_fallback=True) == 0.0

    # Fallback on unanswerable query
    assert compute_correctness(INSUFFICIENT_EVIDENCE_FALLBACK, gold, is_answerable=False, is_fallback=True) == 1.0


def test_compute_completeness():
    """Test entity completeness calculation."""
    entities = ["23CSE302T", "Regulation R23", "Semester VII"]
    answer = "The syllabus for 23CSE302T is under Regulation R23 for Semester VII."
    assert compute_completeness(answer, entities, is_answerable=True, is_fallback=False) == 1.0

    partial_answer = "The syllabus for 23CSE302T under Regulation R23."
    score = compute_completeness(partial_answer, entities, is_answerable=True, is_fallback=False)
    assert pytest.approx(score, 0.001) == 2.0 / 3.0


def test_compute_unsupported_claim_rate():
    """Test unsupported claim rate formula."""
    assert compute_unsupported_claim_rate(1.0) == 0.0
    assert compute_unsupported_claim_rate(0.8) == 0.2
    assert compute_unsupported_claim_rate(0.0) == 1.0
