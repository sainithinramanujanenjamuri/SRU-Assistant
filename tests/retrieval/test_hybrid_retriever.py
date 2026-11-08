"""Unit tests for HybridRetriever coordinator, candidate pooling, and failure semantics."""

from unittest.mock import MagicMock

import pytest

from retrieval.fusion.hybrid import HybridRetriever
from retrieval.lexical.bm25 import BM25Retriever
from retrieval.models import (
    LexicalSearchResult,
    RetrievalError,
    VectorSearchResult,
)
from retrieval.vectorstore.retriever import VectorRetriever


@pytest.fixture
def mock_dense_retriever() -> MagicMock:
    retriever = MagicMock(spec=VectorRetriever)
    retriever.search.return_value = [
        VectorSearchResult(
            chunk_id="chunk_1",
            document_id="doc_1",
            text="Algorithms and data structures",
            cosine_similarity=0.85,
            normalized_score=0.925,
            metadata={"department": "CSE"},
        ),
        VectorSearchResult(
            chunk_id="chunk_2",
            document_id="doc_2",
            text="Academic Calendar mid examinations",
            cosine_similarity=0.60,
            normalized_score=0.80,
            metadata={"department": "All"},
        ),
    ]
    return retriever


@pytest.fixture
def mock_lexical_retriever() -> MagicMock:
    retriever = MagicMock(spec=BM25Retriever)
    retriever.search.return_value = [
        LexicalSearchResult(
            chunk_id="chunk_1",
            document_id="doc_1",
            text="Algorithms and data structures",
            bm25_score=4.5,
            normalized_score=1.0,
            rank=1,
            metadata={"department": "CSE"},
        ),
        LexicalSearchResult(
            chunk_id="chunk_3",
            document_id="doc_3",
            text="Course 23CSE302T syllabus outline",
            bm25_score=3.2,
            normalized_score=0.7,
            rank=2,
            metadata={"department": "CSE"},
        ),
    ]
    return retriever


def test_hybrid_search_normal_fusion(mock_dense_retriever: MagicMock, mock_lexical_retriever: MagicMock):
    """Normal hybrid execution queries both channels and fuses candidate pools."""
    hybrid = HybridRetriever(
        dense_retriever=mock_dense_retriever,
        lexical_retriever=mock_lexical_retriever,
        fusion_method="rrf",
        dense_candidate_k=10,
        lexical_candidate_k=10,
    )

    results = hybrid.search("algorithms", top_k=3)

    assert len(results) == 3
    # Verify both channels were called with candidate_k
    mock_dense_retriever.search.assert_called_once_with(query="algorithms", top_k=10, filters=None)
    mock_lexical_retriever.search.assert_called_once_with(query="algorithms", top_k=10, filters=None)

    # Chunk 1 appears in both channels and should be top ranked
    assert results[0].chunk_id == "chunk_1"
    assert results[0].dense_rank == 1
    assert results[0].lexical_rank == 1
    assert hybrid.last_meta is not None
    assert hybrid.last_meta.actual_mode == "hybrid"
    assert hybrid.last_meta.dense_candidates_retrieved == 2
    assert hybrid.last_meta.lexical_candidates_retrieved == 2


def test_hybrid_explicit_modes(mock_dense_retriever: MagicMock, mock_lexical_retriever: MagicMock):
    """Testing explicit mode overrides: mode='dense' and mode='lexical'."""
    hybrid = HybridRetriever(
        dense_retriever=mock_dense_retriever,
        lexical_retriever=mock_lexical_retriever,
    )

    # Dense-only mode
    dense_res = hybrid.search("test query", top_k=2, mode="dense")
    assert len(dense_res) == 2
    assert hybrid.last_meta is not None
    assert hybrid.last_meta.actual_mode == "dense"

    # Lexical-only mode
    lex_res = hybrid.search("test query", top_k=2, mode="lexical")
    assert len(lex_res) == 2
    assert hybrid.last_meta is not None
    assert hybrid.last_meta.actual_mode == "lexical"


def test_hybrid_channel_failure_without_fallback(
    mock_dense_retriever: MagicMock, mock_lexical_retriever: MagicMock
):
    """When allow_channel_fallback=False, failure of either channel raises RetrievalError."""
    mock_dense_retriever.search.side_effect = RuntimeError("Database connection lost")

    hybrid = HybridRetriever(
        dense_retriever=mock_dense_retriever,
        lexical_retriever=mock_lexical_retriever,
        allow_channel_fallback=False,
    )

    with pytest.raises(RetrievalError):
        hybrid.search("test query")


def test_hybrid_channel_failure_with_fallback(
    mock_dense_retriever: MagicMock, mock_lexical_retriever: MagicMock
):
    """When allow_channel_fallback=True, single-channel failure falls back cleanly."""
    mock_dense_retriever.search.side_effect = RuntimeError("Vector DB unreachable")

    hybrid = HybridRetriever(
        dense_retriever=mock_dense_retriever,
        lexical_retriever=mock_lexical_retriever,
        allow_channel_fallback=True,
    )

    results = hybrid.search("test query", top_k=2)
    assert len(results) == 2
    assert hybrid.last_meta is not None
    assert hybrid.last_meta.actual_mode == "lexical_fallback"


def test_hybrid_both_channels_fail(
    mock_dense_retriever: MagicMock, mock_lexical_retriever: MagicMock
):
    """When both channels fail, strictly raise RetrievalError regardless of fallback flag."""
    mock_dense_retriever.search.side_effect = RuntimeError("Dense down")
    mock_lexical_retriever.search.side_effect = RuntimeError("Lexical down")

    hybrid = HybridRetriever(
        dense_retriever=mock_dense_retriever,
        lexical_retriever=mock_lexical_retriever,
        allow_channel_fallback=True,
    )

    with pytest.raises(RetrievalError) as excinfo:
        hybrid.search("test query")
    assert "Both dense and lexical retrieval channels failed" in str(excinfo.value)


def test_hybrid_both_channels_empty(
    mock_dense_retriever: MagicMock, mock_lexical_retriever: MagicMock
):
    """Case E: both channels return 0 candidates -> returns empty list without error."""
    mock_dense_retriever.search.return_value = []
    mock_lexical_retriever.search.return_value = []

    hybrid = HybridRetriever(
        dense_retriever=mock_dense_retriever,
        lexical_retriever=mock_lexical_retriever,
    )

    results = hybrid.search("unmatched query", top_k=5)
    assert results == []
    assert hybrid.last_meta is not None
    assert hybrid.last_meta.fused_candidates_count == 0
