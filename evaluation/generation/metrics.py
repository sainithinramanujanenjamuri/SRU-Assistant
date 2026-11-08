"""Generation quality and RAG Triad evaluation metrics.

Implements:
1. Groundedness (Faithfulness)
2. Answer Relevance
3. Context Relevance
4. Correctness (Token F1 / Semantic overlap with gold standard)
5. Completeness (Entity coverage)
6. Unsupported Claim Rate
"""
from __future__ import annotations



import re
from typing import Sequence

from citations.models import ClaimItem
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK


def _tokenize(text: str) -> list[str]:
    """Tokenize lowercase alphanumeric words."""
    return re.findall(r"\b[a-zA-Z0-9_\-\.]+\b", text.lower())


def compute_groundedness(
    claims: Sequence[ClaimItem] | None,
    actual_answer: str,
    is_fallback: bool,
) -> float:
    """Compute Groundedness (Faithfulness): proportion of factual claims supported by evidence.

    Formula:
        Groundedness = |Supported Claims| / |Total Factual Claims|

    If answer is the standardized fallback (no-answer response), groundedness is 1.0
    since no unsupported claims are presented.
    """
    if is_fallback or actual_answer.strip() == INSUFFICIENT_EVIDENCE_FALLBACK:
        return 1.0

    if not claims:
        # If no extractable factual claims, default to 1.0 (no unsupported claims)
        return 1.0

    factual_claims = [c for c in claims if c.claim_type in ("factual", "date", "policy", "general")]
    if not factual_claims:
        return 1.0

    supported_count = sum(1 for c in factual_claims if c.is_supported)
    score = supported_count / len(factual_claims)
    return max(0.0, min(1.0, score))


def compute_answer_relevance(
    query: str,
    actual_answer: str,
    is_answerable: bool,
    is_fallback: bool,
) -> float:
    """Compute Answer Relevance: how well the answer addresses the query intent.

    For unanswerable queries:
        Returning the standardized fallback yields 1.0 (perfect compliance).
        Generating an answer yields 0.0 (hallucinated response).

    For answerable queries:
        Returning fallback yields 0.0 (false negative).
        Otherwise computes substantive lexical/entity alignment between query and answer.
    """
    if not is_answerable:
        return 1.0 if is_fallback else 0.0

    if is_fallback:
        return 0.0

    query_tokens = set(_tokenize(query))
    # Remove common English stop words from query intent check
    stop_words = {
        "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "the", "a", "an", "and", "or", "but", "in", "on",
        "at", "to", "for", "with", "about", "against", "between", "into", "through",
        "during", "before", "after", "above", "below", "from", "up", "down", "of",
        "off", "over", "under", "again", "further", "then", "once", "here", "there",
        "all", "any", "both", "each", "few", "more", "most", "other", "some", "such",
        "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very", "can",
        "will", "just", "should", "now", "tell", "me"
    }
    content_query_tokens = query_tokens - stop_words
    if not content_query_tokens:
        content_query_tokens = query_tokens

    answer_tokens = set(_tokenize(actual_answer))
    if not answer_tokens:
        return 0.0

    overlap = len(content_query_tokens.intersection(answer_tokens))
    score = overlap / len(content_query_tokens)
    return max(0.0, min(1.0, score))


def compute_context_relevance(
    retrieved_chunk_ids: Sequence[str],
    expected_chunk_ids: Sequence[str],
) -> float:
    """Compute Context Relevance: proportion of context chunks that contain ground-truth evidence.

    Formula:
        Context Relevance = |Retrieved ∩ Expected| / |Retrieved|
    """
    if not retrieved_chunk_ids:
        return 1.0 if len(expected_chunk_ids) == 0 else 0.0

    expected_set = set(expected_chunk_ids)
    if not expected_set:
        # Out-of-knowledge-base expectation
        return 0.0

    hits = sum(1 for cid in retrieved_chunk_ids if cid in expected_set)
    score = hits / len(retrieved_chunk_ids)
    return max(0.0, min(1.0, score))


def compute_correctness(
    actual_answer: str,
    expected_answer: str,
    is_answerable: bool,
    is_fallback: bool,
) -> float:
    """Compute factual correctness via token F1 against the gold-standard answer."""
    if not is_answerable:
        return 1.0 if is_fallback else 0.0

    if is_fallback:
        return 0.0

    actual_tokens = _tokenize(actual_answer)
    expected_tokens = _tokenize(expected_answer)

    if not actual_tokens or not expected_tokens:
        return 0.0

    actual_set = set(actual_tokens)
    expected_set = set(expected_tokens)

    common = actual_set.intersection(expected_set)
    if not common:
        return 0.0

    precision = len(common) / len(actual_set)
    recall = len(common) / len(expected_set)
    f1 = 2 * (precision * recall) / (precision + recall)
    return max(0.0, min(1.0, f1))


def compute_completeness(
    actual_answer: str,
    expected_entities: Sequence[str],
    is_answerable: bool,
    is_fallback: bool,
) -> float:
    """Compute entity completeness: proportion of required gold-standard entities present in answer."""
    if not is_answerable:
        return 1.0 if is_fallback else 0.0

    if not expected_entities:
        return 1.0

    if is_fallback:
        return 0.0

    lower_answer = actual_answer.lower()
    hits = sum(1 for ent in expected_entities if ent.lower() in lower_answer)
    score = hits / len(expected_entities)
    return max(0.0, min(1.0, score))


def compute_unsupported_claim_rate(groundedness: float) -> float:
    """Compute Unsupported Claim Rate = 1.0 - Groundedness."""
    rate = 1.0 - groundedness
    return round(max(0.0, min(1.0, rate)), 4)
