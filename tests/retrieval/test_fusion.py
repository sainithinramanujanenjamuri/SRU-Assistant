"""Unit tests for ReciprocalRankFusion and WeightedScoreFusion."""

import pytest

from retrieval.fusion.rrf import ReciprocalRankFusion
from retrieval.fusion.weighted import WeightedScoreFusion
from retrieval.models import LexicalSearchResult, VectorSearchResult


@pytest.fixture
def dummy_dense_results() -> list[VectorSearchResult]:
    return [
        VectorSearchResult(
            chunk_id="chunk_A",
            document_id="doc_1",
            text="Text A",
            cosine_similarity=0.8,
            normalized_score=0.9,
            metadata={"department": "CSE"},
        ),
        VectorSearchResult(
            chunk_id="chunk_B",
            document_id="doc_1",
            text="Text B",
            cosine_similarity=0.6,
            normalized_score=0.8,
            metadata={"department": "CSE"},
        ),
        VectorSearchResult(
            chunk_id="chunk_C",
            document_id="doc_2",
            text="Text C",
            cosine_similarity=0.4,
            normalized_score=0.7,
            metadata={"department": "ECE"},
        ),
    ]


@pytest.fixture
def dummy_lexical_results() -> list[LexicalSearchResult]:
    return [
        LexicalSearchResult(
            chunk_id="chunk_B",  # Present in both, rank 1 in lexical
            document_id="doc_1",
            text="Text B",
            bm25_score=5.0,
            normalized_score=1.0,
            rank=1,
            metadata={"department": "CSE"},
        ),
        LexicalSearchResult(
            chunk_id="chunk_D",  # Disjoint: present only in lexical
            document_id="doc_3",
            text="Text D",
            bm25_score=3.5,
            normalized_score=0.7,
            rank=2,
            metadata={"department": "ME"},
        ),
        LexicalSearchResult(
            chunk_id="chunk_A",  # Present in both, rank 3 in lexical
            document_id="doc_1",
            text="Text A",
            bm25_score=2.0,
            normalized_score=0.4,
            rank=3,
            metadata={"department": "CSE"},
        ),
    ]


# ==============================================================================
# Reciprocal Rank Fusion (RRF) Tests
# ==============================================================================


def test_rrf_scoring_and_ranking(
    dummy_dense_results: list[VectorSearchResult],
    dummy_lexical_results: list[LexicalSearchResult],
):
    """RRF combines rank reciprocals: 1/(k+rank_d) + 1/(k+rank_l)."""
    rrf = ReciprocalRankFusion(k=60, dense_weight=1.0, lexical_weight=1.0)
    results = rrf.fuse(dummy_dense_results, dummy_lexical_results, top_k=5)

    assert len(results) == 4  # A, B, C, D
    # Chunk B is rank 2 in dense, rank 1 in lexical:
    # RRF(B) = 1/(60+2) + 1/(60+1) = 1/62 + 1/61 = 0.016129 + 0.016393 = 0.032522
    # Chunk A is rank 1 in dense, rank 3 in lexical:
    # RRF(A) = 1/(60+1) + 1/(60+3) = 1/61 + 1/63 = 0.016393 + 0.015873 = 0.032266
    # Chunk B should rank #1
    assert results[0].chunk_id == "chunk_B"
    assert results[0].dense_rank == 2
    assert results[0].lexical_rank == 1
    assert results[0].fused_score == round(1 / 62 + 1 / 61, 6)

    # Chunk A should rank #2
    assert results[1].chunk_id == "chunk_A"
    assert results[1].dense_rank == 1
    assert results[1].lexical_rank == 3


def test_rrf_disjoint_candidates(
    dummy_dense_results: list[VectorSearchResult],
    dummy_lexical_results: list[LexicalSearchResult],
):
    """Candidate present in only one modality receives rank=None and single contribution."""
    rrf = ReciprocalRankFusion(k=60)
    results = rrf.fuse(dummy_dense_results, dummy_lexical_results, top_k=5)

    chunk_c = next(r for r in results if r.chunk_id == "chunk_C")
    assert chunk_c.dense_rank == 3
    assert chunk_c.lexical_rank is None
    assert chunk_c.fused_score == round(1 / 63, 6)

    chunk_d = next(r for r in results if r.chunk_id == "chunk_D")
    assert chunk_d.dense_rank is None
    assert chunk_d.lexical_rank == 2
    assert chunk_d.fused_score == round(1 / 62, 6)


def test_rrf_deterministic_tie_breaking():
    """Identical RRF scores must break ties deterministically by chunk_id ASC."""
    rrf = ReciprocalRankFusion(k=60)
    # Two candidates with identical single dense hit
    dense = [
        VectorSearchResult(chunk_id="chunk_Z", document_id="d1", text="Z", cosine_similarity=0.5, normalized_score=0.75),
        VectorSearchResult(chunk_id="chunk_Y", document_id="d1", text="Y", cosine_similarity=0.5, normalized_score=0.75),
    ]
    assert len(rrf.fuse(dense, [], top_k=2)) == 2
    # Rank 1 gets 1/61, rank 2 gets 1/62, so chunk_Z is top.
    # Now let's test exact tie by setting weights or separate modalities:
    res1 = [VectorSearchResult(chunk_id="chunk_M", document_id="d1", text="M", cosine_similarity=0.5, normalized_score=0.75)]
    res2 = [LexicalSearchResult(chunk_id="chunk_L", document_id="d1", text="L", bm25_score=1.0, normalized_score=1.0, rank=1)]
    # With dense_weight=1.0 and lexical_weight=1.0, rank 1 in dense = 1/61; rank 1 in lexical = 1/61
    tied_results = rrf.fuse(res1, res2, top_k=2)
    assert tied_results[0].fused_score == tied_results[1].fused_score
    assert tied_results[0].chunk_id == "chunk_L"  # 'chunk_L' < 'chunk_M'
    assert tied_results[1].chunk_id == "chunk_M"


def test_rrf_invalid_parameters():
    """Validation of invalid k and weight bounds."""
    with pytest.raises(ValueError):
        ReciprocalRankFusion(k=-1)

    with pytest.raises(ValueError):
        ReciprocalRankFusion(dense_weight=-0.1)

    with pytest.raises(ValueError):
        ReciprocalRankFusion(dense_weight=0.0, lexical_weight=0.0)


# ==============================================================================
# Weighted Score Fusion Tests
# ==============================================================================


def test_weighted_fusion_convex_combination(
    dummy_dense_results: list[VectorSearchResult],
    dummy_lexical_results: list[LexicalSearchResult],
):
    """Convex combination: score = alpha * dense + (1 - alpha) * lexical."""
    weighted = WeightedScoreFusion(alpha=0.5)
    results = weighted.fuse(dummy_dense_results, dummy_lexical_results, top_k=5)

    # Chunk B: dense=0.8, lexical=1.0 -> 0.5*0.8 + 0.5*1.0 = 0.9
    chunk_b = next(r for r in results if r.chunk_id == "chunk_B")
    assert chunk_b.fused_score == 0.9
    assert chunk_b.normalized_fused_score == 0.9

    # Chunk A: dense=0.9, lexical=0.4 -> 0.5*0.9 + 0.5*0.4 = 0.65
    chunk_a = next(r for r in results if r.chunk_id == "chunk_A")
    assert chunk_a.fused_score == 0.65

    # Chunk C: dense=0.7, lexical=None (0.0) -> 0.5*0.7 = 0.35
    chunk_c = next(r for r in results if r.chunk_id == "chunk_C")
    assert chunk_c.fused_score == 0.35

    # Chunk D: dense=None (0.0), lexical=0.7 -> 0.5*0.7 = 0.35
    chunk_d = next(r for r in results if r.chunk_id == "chunk_D")
    assert chunk_d.fused_score == 0.35


def test_weighted_fusion_alpha_boundaries(
    dummy_dense_results: list[VectorSearchResult],
    dummy_lexical_results: list[LexicalSearchResult],
):
    """Alpha boundary conditions: alpha=1.0 (dense only) and alpha=0.0 (lexical only)."""
    # Alpha = 1.0 (pure dense)
    dense_only = WeightedScoreFusion(alpha=1.0)
    res_dense = dense_only.fuse(dummy_dense_results, dummy_lexical_results, top_k=5)
    chunk_a = next(r for r in res_dense if r.chunk_id == "chunk_A")
    assert chunk_a.fused_score == 0.9
    chunk_d = next(r for r in res_dense if r.chunk_id == "chunk_D")
    assert chunk_d.fused_score == 0.0  # missing dense score is 0.0

    # Alpha = 0.0 (pure lexical)
    lex_only = WeightedScoreFusion(alpha=0.0)
    res_lex = lex_only.fuse(dummy_dense_results, dummy_lexical_results, top_k=5)
    chunk_b = next(r for r in res_lex if r.chunk_id == "chunk_B")
    assert chunk_b.fused_score == 1.0


def test_weighted_fusion_invalid_alpha():
    """Alpha outside [0.0, 1.0] must raise ValueError."""
    with pytest.raises(ValueError):
        WeightedScoreFusion(alpha=-0.1)

    with pytest.raises(ValueError):
        WeightedScoreFusion(alpha=1.1)
