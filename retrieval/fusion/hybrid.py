"""HybridRetriever coordinating dense semantic and sparse lexical retrieval with candidate fusion."""
from __future__ import annotations


import time
from collections.abc import Sequence
from typing import Any

from app.config.settings import get_settings
from retrieval.base import BaseRetriever
from retrieval.fusion.rrf import ReciprocalRankFusion
from retrieval.fusion.weighted import WeightedScoreFusion
from retrieval.lexical.bm25 import BM25Retriever
from retrieval.models import (
    HybridRetrievalMeta,
    HybridSearchResult,
    LexicalSearchResult,
    RetrievalError,
    VectorSearchResult,
)
from retrieval.vectorstore.retriever import VectorRetriever


class HybridRetriever(BaseRetriever):
    """Coordinates multi-channel retrieval combining dense vector search and BM25 lexical search.


    Features:
    - Candidate pool expansion: retrieves larger pools from dense and lexical channels prior to fusion.
    - Modular fusion: supports Reciprocal Rank Fusion (RRF) and Weighted Score Combination.
    - Explicit channel failure semantics (Cases A through E).
    - Full observability: measures per-channel latency and candidate counts.
    - Multi-mode support: 'hybrid', 'dense' (vector only), or 'lexical' (BM25 only).
    """

    def __init__(
        self,
        dense_retriever: VectorRetriever,
        lexical_retriever: BM25Retriever,
        fusion_method: str = "rrf",
        dense_candidate_k: int = 20,
        lexical_candidate_k: int = 20,
        rrf_k: int = 60,
        dense_weight: float = 0.5,
        lexical_weight: float = 0.5,
        allow_channel_fallback: bool = False,
    ):
        if dense_candidate_k <= 0 or lexical_candidate_k <= 0:
            raise ValueError("Candidate pool sizes must be positive integers")

        self.dense_retriever = dense_retriever
        self.lexical_retriever = lexical_retriever
        self.fusion_method = fusion_method.lower()
        self.dense_candidate_k = dense_candidate_k
        self.lexical_candidate_k = lexical_candidate_k
        self.allow_channel_fallback = allow_channel_fallback

        if self.fusion_method == "rrf":
            self.fusion_engine: ReciprocalRankFusion | WeightedScoreFusion = ReciprocalRankFusion(
                k=rrf_k,
                dense_weight=dense_weight,
                lexical_weight=lexical_weight,
            )
        elif self.fusion_method == "weighted":
            self.fusion_engine = WeightedScoreFusion(alpha=dense_weight)
        else:
            raise ValueError(f"Unknown fusion method '{fusion_method}'. Must be 'rrf' or 'weighted'.")

        self.last_meta: HybridRetrievalMeta | None = None

    @classmethod
    def from_settings(
        cls,
        dense_retriever: VectorRetriever,
        lexical_retriever: BM25Retriever,
    ) -> "HybridRetriever":
        """Instantiate HybridRetriever configured from application settings."""
        settings = get_settings()
        return cls(
            dense_retriever=dense_retriever,
            lexical_retriever=lexical_retriever,
            fusion_method=settings.hybrid_fusion_method,
            dense_candidate_k=settings.hybrid_dense_candidate_k,
            lexical_candidate_k=settings.hybrid_lexical_candidate_k,
            rrf_k=settings.hybrid_rrf_k,
            dense_weight=settings.hybrid_dense_weight,
            lexical_weight=settings.hybrid_lexical_weight,
            allow_channel_fallback=settings.hybrid_allow_fallback,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        mode: str | None = None,
    ) -> list[HybridSearchResult]:
        """Execute retrieval using the specified or default retrieval mode.

        Args:
            query: Query string.
            top_k: Final number of candidates to return.
            filters: Optional metadata pre-filtering constraints applied to both channels.
            mode: Optional override ('hybrid', 'dense', 'lexical'). Defaults to configured mode.

        Returns:
            Ranked list of HybridSearchResult items.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        settings = get_settings()
        requested_mode = (mode or settings.retrieval_mode).lower()

        t_total_0 = time.perf_counter()

        # ----------------------------------------------------------------------
        # Mode 1: Dense-Only
        # ----------------------------------------------------------------------
        if requested_mode == "dense":
            t_dense_0 = time.perf_counter()
            dense_results = self.dense_retriever.search(query=query, top_k=top_k, filters=filters)
            dense_ms = (time.perf_counter() - t_dense_0) * 1000.0
            total_ms = (time.perf_counter() - t_total_0) * 1000.0

            self.last_meta = HybridRetrievalMeta(
                requested_mode="dense",
                actual_mode="dense",
                fusion_method="none",
                dense_candidates_retrieved=len(dense_results),
                lexical_candidates_retrieved=0,
                fused_candidates_count=len(dense_results),
                dense_latency_ms=round(dense_ms, 2),
                lexical_latency_ms=0.0,
                fusion_latency_ms=0.0,
                total_retrieval_latency_ms=round(total_ms, 2),
            )
            return self._wrap_dense_results(dense_results)

        # ----------------------------------------------------------------------
        # Mode 2: Lexical-Only
        # ----------------------------------------------------------------------
        if requested_mode == "lexical":
            t_lex_0 = time.perf_counter()
            lex_results = self.lexical_retriever.search(query=query, top_k=top_k, filters=filters)
            lex_ms = (time.perf_counter() - t_lex_0) * 1000.0
            total_ms = (time.perf_counter() - t_total_0) * 1000.0

            self.last_meta = HybridRetrievalMeta(
                requested_mode="lexical",
                actual_mode="lexical",
                fusion_method="none",
                dense_candidates_retrieved=0,
                lexical_candidates_retrieved=len(lex_results),
                fused_candidates_count=len(lex_results),
                dense_latency_ms=0.0,
                lexical_latency_ms=round(lex_ms, 2),
                fusion_latency_ms=0.0,
                total_retrieval_latency_ms=round(total_ms, 2),
            )
            return self._wrap_lexical_results(lex_results)

        # ----------------------------------------------------------------------
        # Mode 3: Hybrid (Dense + Lexical Candidate Pooling and Fusion)
        # ----------------------------------------------------------------------
        dense_results: list[VectorSearchResult] = []
        lexical_results: list[LexicalSearchResult] = []
        dense_failed = False
        lexical_failed = False
        dense_error: Exception | None = None
        lexical_error: Exception | None = None
        dense_ms = 0.0
        lex_ms = 0.0

        # Execute dense channel
        t_d0 = time.perf_counter()
        try:
            dense_results = self.dense_retriever.search(
                query=query,
                top_k=self.dense_candidate_k,
                filters=filters,
            )
            dense_ms = (time.perf_counter() - t_d0) * 1000.0
        except Exception as e:
            dense_failed = True
            dense_error = e

        # Execute lexical channel
        t_l0 = time.perf_counter()
        try:
            lexical_results = self.lexical_retriever.search(
                query=query,
                top_k=self.lexical_candidate_k,
                filters=filters,
            )
            lex_ms = (time.perf_counter() - t_l0) * 1000.0
        except Exception as e:
            lexical_failed = True
            lexical_error = e

        # Handle Channel Failure Semantics (Amendment 10)
        # Case D: Both channels failed
        if dense_failed and lexical_failed:
            raise RetrievalError(
                f"Both dense and lexical retrieval channels failed. Dense error: {dense_error}; "
                f"Lexical error: {lexical_error}"
            )

        # Case B: Dense failed, BM25 succeeded
        if dense_failed and not lexical_failed:
            if not self.allow_channel_fallback:
                raise RetrievalError(f"Dense retrieval channel failed: {dense_error}") from dense_error
            actual_mode = "lexical_fallback"
            total_ms = (time.perf_counter() - t_total_0) * 1000.0
            truncated_lex = lexical_results[:top_k]
            self.last_meta = HybridRetrievalMeta(
                requested_mode="hybrid",
                actual_mode=actual_mode,
                fusion_method="none",
                dense_candidates_retrieved=0,
                lexical_candidates_retrieved=len(lexical_results),
                fused_candidates_count=len(truncated_lex),
                dense_latency_ms=0.0,
                lexical_latency_ms=round(lex_ms, 2),
                fusion_latency_ms=0.0,
                total_retrieval_latency_ms=round(total_ms, 2),
            )
            return self._wrap_lexical_results(truncated_lex)

        # Case C: BM25 failed, Dense succeeded
        if lexical_failed and not dense_failed:
            if not self.allow_channel_fallback:
                raise RetrievalError(f"BM25 lexical retrieval channel failed: {lexical_error}") from lexical_error
            actual_mode = "dense_fallback"
            total_ms = (time.perf_counter() - t_total_0) * 1000.0
            truncated_dense = dense_results[:top_k]
            self.last_meta = HybridRetrievalMeta(
                requested_mode="hybrid",
                actual_mode=actual_mode,
                fusion_method="none",
                dense_candidates_retrieved=len(dense_results),
                lexical_candidates_retrieved=0,
                fused_candidates_count=len(truncated_dense),
                dense_latency_ms=round(dense_ms, 2),
                lexical_latency_ms=0.0,
                fusion_latency_ms=0.0,
                total_retrieval_latency_ms=round(total_ms, 2),
            )
            return self._wrap_dense_results(truncated_dense)

        # Case E: Both succeeded, but returned 0 results
        if not dense_results and not lexical_results:
            total_ms = (time.perf_counter() - t_total_0) * 1000.0
            self.last_meta = HybridRetrievalMeta(
                requested_mode="hybrid",
                actual_mode="hybrid",
                fusion_method=self.fusion_method,
                dense_candidates_retrieved=0,
                lexical_candidates_retrieved=0,
                fused_candidates_count=0,
                dense_latency_ms=round(dense_ms, 2),
                lexical_latency_ms=round(lex_ms, 2),
                fusion_latency_ms=0.0,
                total_retrieval_latency_ms=round(total_ms, 2),
            )
            return []

        # Case A: Both channels succeeded -> Candidate Fusion
        t_fuse_0 = time.perf_counter()
        fused = self.fusion_engine.fuse(
            dense_results=dense_results,
            lexical_results=lexical_results,
            top_k=top_k,
        )
        fuse_ms = (time.perf_counter() - t_fuse_0) * 1000.0
        total_ms = (time.perf_counter() - t_total_0) * 1000.0

        self.last_meta = HybridRetrievalMeta(
            requested_mode="hybrid",
            actual_mode="hybrid",
            fusion_method=self.fusion_method,
            dense_candidates_retrieved=len(dense_results),
            lexical_candidates_retrieved=len(lexical_results),
            fused_candidates_count=len(fused),
            dense_latency_ms=round(dense_ms, 2),
            lexical_latency_ms=round(lex_ms, 2),
            fusion_latency_ms=round(fuse_ms, 2),
            total_retrieval_latency_ms=round(total_ms, 2),
        )
        return fused

    @staticmethod
    def _wrap_dense_results(results: Sequence[VectorSearchResult]) -> list[HybridSearchResult]:
        """Wrap standalone VectorSearchResults into HybridSearchResults."""
        wrapped = []
        for rank, res in enumerate(results, start=1):
            wrapped.append(
                HybridSearchResult(
                    chunk_id=res.chunk_id,
                    document_id=res.document_id,
                    text=res.text,
                    fused_score=res.normalized_score,
                    normalized_fused_score=res.normalized_score,
                    dense_score=res.normalized_score,
                    dense_rank=rank,
                    lexical_score=None,
                    lexical_rank=None,
                    fusion_method="dense_passthrough",
                    metadata=res.metadata,
                    provenance=res.provenance,
                )
            )
        return wrapped

    @staticmethod
    def _wrap_lexical_results(results: Sequence[LexicalSearchResult]) -> list[HybridSearchResult]:
        """Wrap standalone LexicalSearchResults into HybridSearchResults."""
        wrapped = []
        for rank, res in enumerate(results, start=1):
            wrapped.append(
                HybridSearchResult(
                    chunk_id=res.chunk_id,
                    document_id=res.document_id,
                    text=res.text,
                    fused_score=res.normalized_score,
                    normalized_fused_score=res.normalized_score,
                    dense_score=None,
                    dense_rank=None,
                    lexical_score=res.normalized_score,
                    lexical_rank=rank,
                    fusion_method="lexical_passthrough",
                    metadata=res.metadata,
                    provenance=res.provenance,
                )
            )
        return wrapped
