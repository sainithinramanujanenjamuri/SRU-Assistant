"""Unit tests for retrieval evaluation metrics (Recall@K, Precision@K, MRR, nDCG@K)."""

import pytest

from evaluation.retrieval.metrics import (
    compute_mrr,
    compute_ndcg_at_k,
    compute_precision_at_k,
    compute_recall_at_k,
)


def test_compute_recall_at_k():
    """Test Recall@K calculations across various hit distributions."""
    retrieved = ["c1", "c2", "c3", "c4", "c5"]
    expected = ["c2", "c4"]

    # At K=1, only "c1" retrieved -> 0 hits out of 2 expected
    assert compute_recall_at_k(retrieved, expected, k=1) == 0.0

    # At K=2, "c1", "c2" -> 1 hit out of 2 expected
    assert compute_recall_at_k(retrieved, expected, k=2) == 0.5

    # At K=4, "c1", "c2", "c3", "c4" -> 2 hits out of 2 expected
    assert compute_recall_at_k(retrieved, expected, k=4) == 1.0

    # At K=5 -> 2 hits out of 2 expected
    assert compute_recall_at_k(retrieved, expected, k=5) == 1.0

    # Boundary K <= 0
    assert compute_recall_at_k(retrieved, expected, k=0) == 0.0

    # Out of KB (empty expected)
    assert compute_recall_at_k([], [], k=5) == 1.0
    assert compute_recall_at_k(["c1"], [], k=5) == 0.0


def test_compute_precision_at_k():
    """Test Precision@K calculations."""
    retrieved = ["c1", "c2", "c3", "c4", "c5"]
    expected = ["c1", "c3"]

    # K=1: retrieved "c1" (1 hit / 1)
    assert compute_precision_at_k(retrieved, expected, k=1) == 1.0

    # K=2: retrieved "c1", "c2" (1 hit / 2)
    assert compute_precision_at_k(retrieved, expected, k=2) == 0.5

    # K=3: retrieved "c1", "c2", "c3" (2 hits / 3)
    assert pytest.approx(compute_precision_at_k(retrieved, expected, k=3), 0.001) == 2.0 / 3.0

    # K=5: 2 hits / 5
    assert compute_precision_at_k(retrieved, expected, k=5) == 0.4

    # Boundary K <= 0
    assert compute_precision_at_k(retrieved, expected, k=0) == 0.0


def test_compute_mrr():
    """Test Mean Reciprocal Rank (MRR)."""
    expected = ["target_chunk"]

    # First position
    assert compute_mrr(["target_chunk", "other1", "other2"], expected) == 1.0

    # Second position
    assert compute_mrr(["other1", "target_chunk", "other2"], expected) == 0.5

    # Third position
    assert pytest.approx(compute_mrr(["other1", "other2", "target_chunk"], expected), 0.001) == 1.0 / 3.0

    # Not found
    assert compute_mrr(["other1", "other2"], expected) == 0.0

    # Out of KB (empty expected)
    assert compute_mrr([], []) == 1.0
    assert compute_mrr(["other"], []) == 0.0


def test_compute_ndcg_at_k():
    """Test nDCG@K calculations."""
    expected = ["c1", "c2"]

    # Ideal ranking: both relevant chunks at top
    ideal_retrieved = ["c1", "c2", "c3", "c4"]
    assert pytest.approx(compute_ndcg_at_k(ideal_retrieved, expected, k=3), 0.001) == 1.0

    # Inverted ranking: non-relevant chunk at top
    suboptimal = ["c3", "c1", "c2", "c4"]
    ndcg_sub = compute_ndcg_at_k(suboptimal, expected, k=3)
    assert 0.0 < ndcg_sub < 1.0

    # Zero hits
    assert compute_ndcg_at_k(["c3", "c4", "c5"], expected, k=3) == 0.0

    # Boundary K <= 0
    assert compute_ndcg_at_k(ideal_retrieved, expected, k=0) == 0.0
