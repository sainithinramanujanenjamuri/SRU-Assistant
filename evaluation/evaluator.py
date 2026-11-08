"""End-to-end evaluation orchestrator and comparative experiment harness (Phase 9).

Executes the four canonical comparative experiments defined in roadmap.md:
- Experiment A: Vector RAG (Dense vector retrieval only)
- Experiment B: Hybrid RAG (Dense + BM25 with RRF fusion)
- Experiment C: Hybrid + Re-ranking (EnhancedRetriever with deterministic reranking)
- Experiment D: Full Grounded Pipeline (Hybrid + Re-ranking + Grounding Validation + Citation Verification)
"""
from __future__ import annotations



import hashlib
import statistics
import time
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from pathlib import Path
from typing import Sequence


from app.config.settings import get_settings
from evaluation.datasets.benchmark_loader import BenchmarkDatasetLoader
from evaluation.generation.evaluator import GenerationEvaluator
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
from evaluation.retrieval.metrics import (
    compute_mrr,
    compute_ndcg_at_k,
    compute_precision_at_k,
    compute_recall_at_k,
)
from generation.llm.factory import get_generator
from generation.pipeline import BaselineRAGPipeline
from generation.prompts.context_builder import ContextBuilder
from retrieval.base import BaseRetriever
from retrieval.embeddings.factory import get_embedding_model
from retrieval.enhanced_retriever import EnhancedRetriever
from retrieval.filtering.metadata_filter import MetadataFilter
from retrieval.fusion.hybrid import HybridRetriever
from retrieval.lexical.bm25 import BM25Retriever
from retrieval.reranking.deterministic import DeterministicCrossFeatureReranker
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


class RAGEvaluator:
    """Orchestrates comprehensive benchmark evaluation and comparative ablation studies."""

    EXPERIMENT_CONFIGS = {
        "A": {
            "name": "Experiment A: Vector RAG",
            "description": "Baseline dense semantic vector retrieval without reranking or grounding remediation",
            "retrieval_mode": "dense",
            "rerank": False,
            "grounding": False,
            "citation_verify": False,
        },
        "B": {
            "name": "Experiment B: Hybrid RAG",
            "description": "Hybrid dense + BM25 lexical retrieval using Reciprocal Rank Fusion",
            "retrieval_mode": "hybrid",
            "rerank": False,
            "grounding": False,
            "citation_verify": False,
        },
        "C": {
            "name": "Experiment C: Hybrid + Re-ranking",
            "description": "Hybrid retrieval with institutional metadata filtering and cross-feature re-ranking",
            "retrieval_mode": "enhanced",
            "rerank": True,
            "grounding": False,
            "citation_verify": False,
        },
        "D": {
            "name": "Experiment D: Full Grounded Pipeline",
            "description": "Complete pipeline with hybrid reranking, conflict detection, grounding validation, and citation verification",
            "retrieval_mode": "enhanced",
            "rerank": True,
            "grounding": True,
            "citation_verify": True,
        },
    }

    def __init__(
        self,
        loader: BenchmarkDatasetLoader | None = None,
        db_path: str | Path | None = None,
        bm25_path: str | Path | None = None,
        k_values: tuple[int, ...] = (1, 3, 5),
    ):
        settings = get_settings()
        self.loader = loader or BenchmarkDatasetLoader()
        self.db_path = str(db_path or settings.vectorstore_path)
        self.bm25_path = Path(bm25_path or settings.bm25_index_path)
        self.k_values = k_values
        self.gen_evaluator = GenerationEvaluator()

        # Shared retriever components
        self.embedding_model = get_embedding_model()
        self.vector_store = SQLiteVectorStore(db_path=self.db_path)
        self.dense_retriever = VectorRetriever(
            embedding_model=self.embedding_model,
            vector_store=self.vector_store,
        )

        if self.bm25_path.exists():
            self.lexical_retriever = BM25Retriever.from_file(index_path=self.bm25_path)
        else:
            self.lexical_retriever = None

        self.hybrid_retriever = (
            HybridRetriever(
                dense_retriever=self.dense_retriever,
                lexical_retriever=self.lexical_retriever,
                fusion_method=settings.hybrid_fusion_method,
            )
            if self.lexical_retriever
            else None
        )

        self.enhanced_retriever = (
            EnhancedRetriever(
                hybrid_retriever=self.hybrid_retriever or self.dense_retriever,
                metadata_filter=MetadataFilter(mode=settings.retrieval_filter_mode),
                reranker=DeterministicCrossFeatureReranker(),
                candidate_k=settings.reranker_candidate_k,
                filter_mode=settings.retrieval_filter_mode,
                enable_reranking=True,
            )
            if self.hybrid_retriever
            else None
        )

    def _build_pipeline_for_experiment(
        self,
        exp_key: str,
        generator_provider: str = "deterministic",
        generator_model: str | None = None,
    ) -> BaselineRAGPipeline:
        """Construct an isolated BaselineRAGPipeline instance for the specified experiment."""
        cfg = self.EXPERIMENT_CONFIGS[exp_key]
        mode = cfg["retrieval_mode"]
        retriever: BaseRetriever

        if mode == "dense":
            retriever = self.dense_retriever
        elif mode == "hybrid":
            retriever = self.hybrid_retriever or self.dense_retriever
        elif mode == "enhanced":
            retriever = self.enhanced_retriever or self.dense_retriever
        else:
            retriever = self.dense_retriever

        generator = get_generator(provider=generator_provider, model=generator_model)
        pipeline = BaselineRAGPipeline(
            retriever=retriever,
            generator=generator,
            context_builder=ContextBuilder(),
        )

        # Toggle experimental features
        pipeline._grounding_validation_enabled = bool(cfg["grounding"])
        pipeline._conflict_detection_enabled = bool(cfg["grounding"])
        pipeline._citation_verification_enabled = bool(cfg["citation_verify"])

        return pipeline

    def evaluate_experiment(
        self,
        exp_key: str,
        queries: Sequence[BenchmarkQuery] | None = None,
        top_k: int = 5,
        generator_provider: str = "deterministic",
        generator_model: str | None = None,
    ) -> ExperimentRunResult:
        """Run full evaluation for a designated experiment configuration."""
        if exp_key not in self.EXPERIMENT_CONFIGS:
            raise ValueError(f"Unknown experiment '{exp_key}'. Expected one of: {list(self.EXPERIMENT_CONFIGS.keys())}")

        cfg = self.EXPERIMENT_CONFIGS[exp_key]
        eval_queries = list(queries) if queries is not None else self.loader.queries
        pipeline = self._build_pipeline_for_experiment(
            exp_key=exp_key,
            generator_provider=generator_provider,
            generator_model=generator_model,
        )

        query_results: list[QueryEvaluationResult] = []
        all_recalls: dict[int, list[float]] = {k: [] for k in self.k_values}
        all_precisions: dict[int, list[float]] = {k: [] for k in self.k_values}
        all_mrr: list[float] = []
        all_ndcg: dict[int, list[float]] = {k: [] for k in (3, 5) if k in self.k_values}

        gen_eval_pairs: list[tuple[GenerationMetrics, CitationMetrics]] = []
        stage_latencies: dict[str, list[float]] = {
            "retrieval": [],
            "context": [],
            "conflict": [],
            "generation": [],
            "grounding": [],
            "citation": [],
            "total": [],
        }

        # Run each query
        for q in eval_queries:
            t0 = time.perf_counter()
            response = pipeline.answer_query(
                query=q.query,
                top_k=top_k,
                verify_citations=cfg["citation_verify"],
            )
            wall_total_ms = (time.perf_counter() - t0) * 1000.0

            retrieved_chunk_ids = [e.chunk_id for e in response.evidence]

            # Compute retrieval metrics
            recall_dict = {
                k: compute_recall_at_k(retrieved_chunk_ids, q.expected_chunk_ids, k)
                for k in self.k_values
            }
            precision_dict = {
                k: compute_precision_at_k(retrieved_chunk_ids, q.expected_chunk_ids, k)
                for k in self.k_values
            }
            mrr = compute_mrr(retrieved_chunk_ids, q.expected_chunk_ids)
            ndcg_dict = {
                k: compute_ndcg_at_k(retrieved_chunk_ids, q.expected_chunk_ids, k)
                for k in (3, 5)
                if k in self.k_values
            }

            for k in self.k_values:
                all_recalls[k].append(recall_dict[k])
                all_precisions[k].append(precision_dict[k])
            all_mrr.append(mrr)
            for k in all_ndcg:
                all_ndcg[k].append(ndcg_dict[k])

            retrieval_m = RetrievalMetrics(
                recall_at_k=recall_dict,
                precision_at_k=precision_dict,
                mrr=round(mrr, 4),
                ndcg_at_k=ndcg_dict,
                latency_ms={"mean": round(response.retrieval_latency_ms, 2)},
            )

            # Compute generation & citation metrics
            gen_m, cit_m = self.gen_evaluator.evaluate_response(response, q)
            gen_eval_pairs.append((gen_m, cit_m))

            # Record latencies
            stage_latencies["retrieval"].append(response.retrieval_latency_ms)
            stage_latencies["context"].append(response.context_latency_ms)
            stage_latencies["conflict"].append(response.conflict_latency_ms)
            stage_latencies["generation"].append(response.generation_latency_ms)
            stage_latencies["grounding"].append(response.grounding_latency_ms)
            stage_latencies["citation"].append(response.citation_latency_ms)
            stage_latencies["total"].append(wall_total_ms)

            latency_bd = LatencyBreakdown(
                retrieval_ms=round(response.retrieval_latency_ms, 2),
                context_ms=round(response.context_latency_ms, 2),
                conflict_ms=round(response.conflict_latency_ms, 2),
                generation_ms=round(response.generation_latency_ms, 2),
                grounding_ms=round(response.grounding_latency_ms, 2),
                citation_ms=round(response.citation_latency_ms, 2),
                total_ms=round(wall_total_ms, 2),
            )

            q_res = QueryEvaluationResult(
                query_id=q.query_id,
                query=q.query,
                category=q.category,
                is_answerable=q.is_answerable,
                expected_behavior=q.expected_behavior,
                actual_answer=response.answer,
                retrieved_chunk_ids=retrieved_chunk_ids,
                retrieval_metrics=retrieval_m,
                generation_metrics=gen_m,
                citation_metrics=cit_m,
                latency=latency_bd,
                passed_grounding=response.is_grounded,
                passed_verification=(
                    response.citation_verification.is_fully_supported
                    if response.citation_verification
                    else True
                ),
            )
            query_results.append(q_res)

        # Compute dataset macro-averages
        count = len(eval_queries)
        macro_recall = {k: round(sum(vals) / count, 4) for k, vals in all_recalls.items()}
        macro_precision = {k: round(sum(vals) / count, 4) for k, vals in all_precisions.items()}
        macro_mrr = round(sum(all_mrr) / count, 4)
        macro_ndcg = {k: round(sum(vals) / count, 4) for k, vals in all_ndcg.items()}

        agg_retrieval = RetrievalMetrics(
            recall_at_k=macro_recall,
            precision_at_k=macro_precision,
            mrr=macro_mrr,
            ndcg_at_k=macro_ndcg,
        )

        agg_generation, agg_citation = self.gen_evaluator.aggregate_metrics(gen_eval_pairs)

        # Latency distributions across stages
        agg_latencies: dict[str, dict[str, float]] = {}
        for stage, lats in stage_latencies.items():
            if lats:
                s_sorted = sorted(lats)
                p95_idx = min(int(0.95 * len(s_sorted)), len(s_sorted) - 1)
                agg_latencies[stage] = {
                    "mean": round(statistics.mean(lats), 2),
                    "median": round(statistics.median(lats), 2),
                    "p95": round(s_sorted[p95_idx], 2),
                }
            else:
                agg_latencies[stage] = {"mean": 0.0, "median": 0.0, "p95": 0.0}

        # Category Breakdown
        category_metrics: dict[str, dict[str, Any]] = {}
        for cat in CANONICAL_BENCHMARK_CATEGORIES:
            cat_results = [r for r in query_results if r.category == cat]
            if cat_results:
                c_len = len(cat_results)
                c_r5 = sum(r.retrieval_metrics.recall_at_k.get(5, 0.0) for r in cat_results) / c_len
                c_mrr = sum(r.retrieval_metrics.mrr for r in cat_results) / c_len
                c_grd = sum(r.generation_metrics.groundedness for r in cat_results) / c_len
                c_ans = sum(r.generation_metrics.answer_relevance for r in cat_results) / c_len
                c_cor = sum(r.generation_metrics.correctness for r in cat_results) / c_len
                c_unsupp = sum(r.generation_metrics.unsupported_claim_rate for r in cat_results) / c_len
                category_metrics[cat] = {
                    "count": c_len,
                    "recall_at_5": round(c_r5, 4),
                    "mrr": round(c_mrr, 4),
                    "groundedness": round(c_grd, 4),
                    "answer_relevance": round(c_ans, 4),
                    "correctness": round(c_cor, 4),
                    "unsupported_claim_rate": round(c_unsupp, 4),
                }

        return ExperimentRunResult(
            experiment_id=exp_key,
            name=cfg["name"],
            description=cfg["description"],
            retrieval_mode=cfg["retrieval_mode"],
            reranking_enabled=cfg["rerank"],
            grounding_validation_enabled=cfg["grounding"],
            citation_verification_enabled=cfg["citation_verify"],
            total_queries=count,
            aggregate_retrieval=agg_retrieval,
            aggregate_generation=agg_generation,
            aggregate_citation=agg_citation,
            aggregate_latency_ms=agg_latencies,
            category_metrics=category_metrics,
            query_results=query_results,
        )

    def run_all_experiments(
        self,
        experiment_keys: Sequence[str] = ("A", "B", "C", "D"),
        queries: Sequence[BenchmarkQuery] | None = None,
        top_k: int = 5,
        generator_provider: str = "deterministic",
        generator_model: str | None = None,
    ) -> EvaluationReport:
        """Execute comparative evaluation across designated experiments."""
        eval_queries = list(queries) if queries is not None else self.loader.queries
        experiment_results: dict[str, ExperimentRunResult] = {}

        for key in experiment_keys:
            res = self.evaluate_experiment(
                exp_key=key,
                queries=eval_queries,
                top_k=top_k,
                generator_provider=generator_provider,
                generator_model=generator_model,
            )
            experiment_results[key] = res

        report_raw = f"{self.loader.dataset_hash}_{datetime.now(UTC).isoformat()}"
        report_id = f"eval_report_{hashlib.sha256(report_raw.encode('utf-8')).hexdigest()[:12]}"

        return EvaluationReport(
            report_id=report_id,
            generated_at=datetime.now(UTC).isoformat(),
            dataset_version=self.loader.dataset_version,
            dataset_hash=self.loader.dataset_hash,
            total_queries=len(eval_queries),
            category_distribution=self.loader.get_category_distribution(),
            experiments=experiment_results,
        )
