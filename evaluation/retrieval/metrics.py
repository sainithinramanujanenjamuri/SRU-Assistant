"""Information Retrieval metrics (Recall@K, Precision@K, MRR, nDCG@K).

Provides mathematically rigorous, boundary-validated IR metrics for benchmark evaluation.
"""

import math
from typing import Sequence


def compute_recall_at_k(
    retrieved_chunk_ids: Sequence[str],
    expected_chunk_ids: Sequence[str],
    k: int,
) -> float:
    """Compute Recall@K: proportion of expected relevant chunks retrieved in top K results.

    Formula:
        Recall@K = |Retrieved[:k] ∩ Expected| / |Expected|

    If expected_chunk_ids is empty (e.g. out-of-knowledge-base query),
    returns 1.0 if no chunks were retrieved, or 0.0 if irrelevant chunks were retrieved.
    """
    if k <= 0:
        return 0.0

    expected_set = set(expected_chunk_ids)
    if not expected_set:
        # Out-of-knowledge-base expectation
        return 1.0 if len(retrieved_chunk_ids) == 0 else 0.0

    top_k_set = set(retrieved_chunk_ids[:k])
    hits = len(top_k_set.intersection(expected_set))
    score = hits / len(expected_set)
    return max(0.0, min(1.0, score))


def compute_precision_at_k(
    retrieved_chunk_ids: Sequence[str],
    expected_chunk_ids: Sequence[str],
    k: int,
) -> float:
    """Compute Precision@K: proportion of top K retrieved results that are relevant.

    Formula:
        Precision@K = |Retrieved[:k] ∩ Expected| / k
    """
    if k <= 0:
        return 0.0

    expected_set = set(expected_chunk_ids)
    if not expected_set:
        # Out-of-knowledge-base query
        return 1.0 if len(retrieved_chunk_ids) == 0 else 0.0

    top_k_items = retrieved_chunk_ids[:k]
    if not top_k_items:
        return 0.0

    hits = sum(1 for cid in top_k_items if cid in expected_set)
    score = hits / k
    return max(0.0, min(1.0, score))


def compute_mrr(
    retrieved_chunk_ids: Sequence[str],
    expected_chunk_ids: Sequence[str],
) -> float:
    """Compute Mean Reciprocal Rank (MRR): reciprocal rank of first relevant chunk.

    Formula:
        RR = 1 / rank_first_relevant (1-indexed), or 0.0 if not found.
    """
    expected_set = set(expected_chunk_ids)
    if not expected_set:
        return 1.0 if len(retrieved_chunk_ids) == 0 else 0.0

    for idx, cid in enumerate(retrieved_chunk_ids):
        if cid in expected_set:
            return 1.0 / (idx + 1)

    return 0.0


def compute_ndcg_at_k(
    retrieved_chunk_ids: Sequence[str],
    expected_chunk_ids: Sequence[str],
    k: int,
) -> float:
    """Compute Normalized Discounted Cumulative Gain at rank K (nDCG@K).

    Formula:
        DCG@K = sum_{i=1}^K (rel_i / log2(i + 1))
        IDCG@K = sum_{j=1}^min(K, |Expected|) (1 / log2(j + 1))
        nDCG@K = DCG@K / IDCG@K
    """
    if k <= 0:
        return 0.0

    expected_set = set(expected_chunk_ids)
    if not expected_set:
        return 1.0 if len(retrieved_chunk_ids) == 0 else 0.0

    # Calculate DCG@K
    dcg = 0.0
    for idx, cid in enumerate(retrieved_chunk_ids[:k]):
        rel = 1.0 if cid in expected_set else 0.0
        if rel > 0.0:
            rank = idx + 1
            dcg += rel / math.log2(rank + 1)

    # Calculate Ideal DCG@K (all relevant items at top)
    ideal_hits = min(k, len(expected_set))
    if ideal_hits == 0:
        return 0.0

    idcg = sum(1.0 / math.log2(j + 2) for j in range(ideal_hits))
    if idcg <= 0.0:
        return 0.0

    score = dcg / idcg
    return max(0.0, min(1.0, score))
