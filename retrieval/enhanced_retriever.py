"""EnhancedRetriever coordinating query analysis, hybrid candidate retrieval, metadata filtering, and re-ranking."""
from __future__ import annotations


import time
from typing import Any

from app.config.settings import get_settings
from retrieval.base import BaseRetriever
from retrieval.filtering.metadata_filter import MetadataFilter
from retrieval.models import EnhancedRetrievalMeta, RerankResult
from retrieval.query.analyzer import AcademicQueryAnalyzer
from retrieval.reranking.base import BaseReranker
from retrieval.reranking.deterministic import DeterministicCrossFeatureReranker
from retrieval.reranking.factory import get_reranker
from retrieval.reranking.passthrough import PassthroughReranker


class EnhancedRetriever(BaseRetriever):
    """Multi-stage enhanced retriever coordinating query analysis, metadata filtering, and re-ranking.


    Pipeline Architecture:
        1. Academic Query Analysis (Deterministic entity & intent extraction, suggested filters)
        2. Candidate Pool Retrieval (Hybrid Dense + BM25 search with expanded candidate_k)
        3. Metadata Filtering (Soft score adjustment or hard eligibility pruning, null-safe global evidence)
        4. Cross-Feature / Neural Re-ranking (Joint Query + Passage evaluation)
        5. Top-K Selection (Deterministic tie-breaking)

    Conforms to BaseRetriever protocol for seamless drop-in integration with BaselineRAGPipeline.
    """

    retrieval_mode: str = "enhanced"

    def __init__(
        self,
        hybrid_retriever: BaseRetriever,
        reranker: BaseReranker | None = None,
        query_analyzer: AcademicQueryAnalyzer | None = None,
        metadata_filter: MetadataFilter | None = None,
        candidate_k: int = 20,
        filter_mode: str = "soft",
        enable_query_analysis: bool = True,
        enable_reranking: bool = True,
        allow_reranker_fallback: bool = False,
    ):
        if candidate_k <= 0:
            raise ValueError(f"candidate_k must be a positive integer, got {candidate_k}")

        self.hybrid_retriever = hybrid_retriever
        self.reranker = reranker or DeterministicCrossFeatureReranker()
        self.query_analyzer = query_analyzer or AcademicQueryAnalyzer()
        self.metadata_filter = metadata_filter or MetadataFilter(mode=filter_mode)
        self.candidate_k = candidate_k
        self.filter_mode = filter_mode.lower()
        self.enable_query_analysis = enable_query_analysis
        self.enable_reranking = enable_reranking
        self.allow_reranker_fallback = allow_reranker_fallback

        self.last_meta: EnhancedRetrievalMeta | None = None

    @classmethod
    def from_settings(
        cls,
        hybrid_retriever: BaseRetriever,
        reranker: BaseReranker | None = None,
    ) -> "EnhancedRetriever":
        """Instantiate an EnhancedRetriever configured from application settings."""
        settings = get_settings()
        target_reranker = reranker or get_reranker(
            method=settings.reranker_type,
            model_name=settings.reranker_model_name,
        )
        return cls(
            hybrid_retriever=hybrid_retriever,
            reranker=target_reranker,
            candidate_k=settings.reranker_candidate_k,
            filter_mode=settings.retrieval_filter_mode,
            enable_query_analysis=settings.query_analysis_enabled,
            enable_reranking=settings.retrieval_reranking_enabled,
            allow_reranker_fallback=settings.allow_reranker_fallback,
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        filter_mode: str | None = None,
        rerank: bool | None = None,
    ) -> list[RerankResult]:
        """Execute multi-stage enhanced retrieval.

        Args:
            query: User search query string.
            top_k: Final number of evidence chunks to return.
            filters: Optional metadata filtering constraints.
            filter_mode: Optional filter mode override ('soft' or 'hard').
            rerank: Optional toggle overriding enable_reranking.

        Returns:
            List of RerankResult instances ordered deterministically.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        cleaned_query = query.strip()
        t_total_0 = time.perf_counter()

        # Step 1: Academic Query Analysis
        t_qa_0 = time.perf_counter()
        query_analysis_res = None
        effective_filters: dict[str, Any] = dict(filters or {})

        if self.enable_query_analysis:
            query_analysis_res = self.query_analyzer.analyze(cleaned_query)
            # If caller did not provide explicit filters, adopt non-destructive suggested filters
            if not filters and query_analysis_res.suggested_filters:
                effective_filters.update(query_analysis_res.suggested_filters)
        qa_ms = (time.perf_counter() - t_qa_0) * 1000.0

        # Step 2: Hybrid Candidate Retrieval (expanded candidate pool K = 20)
        t_ret_0 = time.perf_counter()
        search_query = (
            query_analysis_res.expanded_query
            if query_analysis_res and query_analysis_res.expanded_query
            else cleaned_query
        )
        candidate_pool = self.hybrid_retriever.search(
            query=search_query,
            top_k=max(self.candidate_k, top_k),
            filters=None,
        )

        ret_ms = (time.perf_counter() - t_ret_0) * 1000.0
        initial_candidate_count = len(candidate_pool)

        if not candidate_pool:
            total_ms = (time.perf_counter() - t_total_0) * 1000.0
            self.last_meta = EnhancedRetrievalMeta(
                query_analysis_latency_ms=round(qa_ms, 2),
                candidate_retrieval_latency_ms=round(ret_ms, 2),
                metadata_filter_latency_ms=0.0,
                reranking_latency_ms=0.0,
                total_retrieval_latency_ms=round(total_ms, 2),
                initial_candidate_count=0,
                post_filter_count=0,
                final_count=0,
                retrieval_mode="enhanced",
                filter_mode=filter_mode or self.filter_mode,
                reranker_name=self.reranker.reranker_name,
                reranker_provider=self.reranker.reranker_provider,
                reranker_model=self.reranker.reranker_model,
                query_analysis_result=query_analysis_res,
            )
            return []

        # Step 3: Metadata Filtering
        t_filt_0 = time.perf_counter()
        active_filter_mode = (filter_mode or self.filter_mode).lower()
        filtered_candidates = self.metadata_filter.filter_candidates(
            candidates=candidate_pool,
            filters=effective_filters,
            mode_override=active_filter_mode,
        )
        filt_ms = (time.perf_counter() - t_filt_0) * 1000.0
        post_filter_count = len(filtered_candidates)

        if not filtered_candidates:
            total_ms = (time.perf_counter() - t_total_0) * 1000.0
            self.last_meta = EnhancedRetrievalMeta(
                query_analysis_latency_ms=round(qa_ms, 2),
                candidate_retrieval_latency_ms=round(ret_ms, 2),
                metadata_filter_latency_ms=round(filt_ms, 2),
                reranking_latency_ms=0.0,
                total_retrieval_latency_ms=round(total_ms, 2),
                initial_candidate_count=initial_candidate_count,
                post_filter_count=0,
                final_count=0,
                retrieval_mode="enhanced",
                filter_mode=active_filter_mode,
                reranker_name=self.reranker.reranker_name,
                reranker_provider=self.reranker.reranker_provider,
                reranker_model=self.reranker.reranker_model,
                query_analysis_result=query_analysis_res,
            )
            return []

        # Step 4: Re-ranking
        should_rerank = self.enable_reranking if rerank is None else rerank
        t_rerank_0 = time.perf_counter()

        actual_reranker = self.reranker if should_rerank else PassthroughReranker()
        try:
            reranked_results = actual_reranker.rerank(
                query=cleaned_query,
                candidates=filtered_candidates,
                top_k=top_k,
            )
        except Exception:
            if self.allow_reranker_fallback and should_rerank:
                fallback = DeterministicCrossFeatureReranker()
                reranked_results = fallback.rerank(
                    query=cleaned_query,
                    candidates=filtered_candidates,
                    top_k=top_k,
                )
                actual_reranker = fallback
            else:
                raise

        rerank_ms = (time.perf_counter() - t_rerank_0) * 1000.0
        total_ms = (time.perf_counter() - t_total_0) * 1000.0

        # Step 5: Rank movement & observability
        moved_up = 0
        moved_down = 0
        unchanged = 0
        initial_top_k_ids = {getattr(c, "chunk_id", "") for c in filtered_candidates[:top_k]}
        final_top_k_ids = {r.chunk_id for r in reranked_results}

        entered_top_k = len(final_top_k_ids - initial_top_k_ids)
        left_top_k = len(initial_top_k_ids - final_top_k_ids)

        for res in reranked_results:
            if res.rank_delta > 0:
                moved_up += 1
            elif res.rank_delta < 0:
                moved_down += 1
            else:
                unchanged += 1

        self.last_meta = EnhancedRetrievalMeta(
            query_analysis_latency_ms=round(qa_ms, 2),
            candidate_retrieval_latency_ms=round(ret_ms, 2),
            metadata_filter_latency_ms=round(filt_ms, 2),
            reranking_latency_ms=round(rerank_ms, 2),
            total_retrieval_latency_ms=round(total_ms, 2),
            initial_candidate_count=initial_candidate_count,
            post_filter_count=post_filter_count,
            final_count=len(reranked_results),
            moved_up_count=moved_up,
            moved_down_count=moved_down,
            unchanged_count=unchanged,
            entered_top_k_count=entered_top_k,
            left_top_k_count=left_top_k,
            retrieval_mode="enhanced" if should_rerank else "enhanced_no_rerank",
            filter_mode=active_filter_mode,
            reranker_name=actual_reranker.reranker_name,
            reranker_provider=actual_reranker.reranker_provider,
            reranker_model=actual_reranker.reranker_model,
            query_analysis_result=query_analysis_res,
        )

        return reranked_results
