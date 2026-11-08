"""Evaluation harness for Phase 6 Retrieval Enhancement ablation and Top-K tuning experiments."""
from __future__ import annotations



import hashlib
import json
import statistics
import time
from dataclasses import dataclass
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from pathlib import Path
from typing import Any


from app.config.settings import get_settings
from retrieval.embeddings.factory import get_embedding_model
from retrieval.enhanced_retriever import EnhancedRetriever
from retrieval.filtering.metadata_filter import MetadataFilter
from retrieval.fusion.hybrid import HybridRetriever
from retrieval.lexical.bm25 import BM25Retriever
from retrieval.query.analyzer import AcademicQueryAnalyzer
from retrieval.reranking.deterministic import DeterministicCrossFeatureReranker
from retrieval.reranking.passthrough import PassthroughReranker
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


@dataclass(frozen=True)
class BenchmarkQuery:
    """Evaluation query specification with expected relevant chunk IDs and category."""

    query_id: str
    query: str
    expected_chunk_ids: tuple[str, ...]
    category: str
    description: str


# Fixed evaluation dataset across 7 academic categories (Amendment 17)
EVALUATION_DATASET: list[BenchmarkQuery] = [
    BenchmarkQuery(
        query_id="q1_course_code",
        query="What topics are covered in 23CSE302T?",
        expected_chunk_ids=("doc_syllabus_23cse302t_chunk_0001",),
        category="course_code",
        description="Exact alphanumeric course code retrieval",
    ),
    BenchmarkQuery(
        query_id="q2_academic_date",
        query="When are the mid examinations scheduled in the calendar?",
        expected_chunk_ids=("doc_calendar_2026_27_chunk_0000",),
        category="academic_date",
        description="Specific academic examination dates",
    ),
    BenchmarkQuery(
        query_id="q3_regulation",
        query="What is the curriculum under Regulation R23?",
        expected_chunk_ids=("doc_syllabus_23cse302t_chunk_0000",),
        category="regulation",
        description="Institutional academic regulation identifier",
    ),
    BenchmarkQuery(
        query_id="q4_semantic",
        query="What will students learn about graph algorithms and tree traversals?",
        expected_chunk_ids=("doc_syllabus_23cse302t_chunk_0001",),
        category="semantic_paraphrased",
        description="Paraphrased semantic query without course code",
    ),
    BenchmarkQuery(
        query_id="q5_dept_semester",
        query="Computer Science and Engineering Semester VII syllabus overview",
        expected_chunk_ids=("doc_syllabus_23cse302t_chunk_0000",),
        category="department_semester",
        description="Department and semester specific query",
    ),
    BenchmarkQuery(
        query_id="q6_university_calendar",
        query="When does classwork commence for the academic session 2026-27?",
        expected_chunk_ids=("doc_calendar_2026_27_chunk_0000",),
        category="university_calendar",
        description="University-wide global academic calendar event",
    ),
    BenchmarkQuery(
        query_id="q7_exact_term",
        query="Mid-Semester Examination I schedule",
        expected_chunk_ids=("doc_calendar_2026_27_chunk_0000",),
        category="exact_academic_term",
        description="Exact examination title lookup",
    ),
]


def compute_dataset_hash(dataset: list[BenchmarkQuery]) -> str:
    """Compute deterministic SHA-256 hash of the evaluation dataset."""
    canonical_repr = "\n".join(
        f"{q.query_id}|{q.query}|{','.join(q.expected_chunk_ids)}|{q.category}"
        for q in dataset
    )
    return hashlib.sha256(canonical_repr.encode("utf-8")).hexdigest()


class RetrievalEnhancementBenchmark:
    """Automated benchmark evaluating Phase 6 ablations and Top-K configurations."""

    DATASET_VERSION: str = "1.0.0"

    def __init__(
        self,
        dataset: list[BenchmarkQuery] | None = None,
        top_k_values: tuple[int, ...] = (3, 5, 10, 15),
    ):
        self.dataset = dataset or EVALUATION_DATASET
        self.dataset_hash = compute_dataset_hash(self.dataset)
        self.top_k_values = top_k_values

    def _init_retrievers(self) -> dict[str, Any]:
        """Instantiate underlying retrievers from persisted vector store and BM25 index."""
        settings = get_settings()
        embedding_model = get_embedding_model()
        vector_store = SQLiteVectorStore(db_path=settings.vectorstore_path)
        dense_retriever = VectorRetriever(embedding_model=embedding_model, vector_store=vector_store)
        lexical_retriever = BM25Retriever.from_file(index_path=settings.bm25_index_path)

        hybrid_retriever = HybridRetriever(
            dense_retriever=dense_retriever,
            lexical_retriever=lexical_retriever,
            fusion_method="rrf",
            dense_candidate_k=20,
            lexical_candidate_k=20,
        )

        query_analyzer = AcademicQueryAnalyzer()
        deterministic_reranker = DeterministicCrossFeatureReranker()
        passthrough_reranker = PassthroughReranker()

        return {
            "dense_retriever": dense_retriever,
            "lexical_retriever": lexical_retriever,
            "hybrid_retriever": hybrid_retriever,
            "query_analyzer": query_analyzer,
            "deterministic_reranker": deterministic_reranker,
            "passthrough_reranker": passthrough_reranker,
        }

    def run_benchmark(self, num_runs_per_query: int = 3) -> dict[str, Any]:
        """Execute full benchmark across ablations and Top-K values.

        Evaluates configurations A through F (Amendment 15):
            A. Dense Only
            B. BM25 Only
            C. Hybrid (RRF)
            D. Hybrid + Metadata Filtering
            E. Hybrid + Re-ranking
            F. Hybrid + Metadata Filtering + Re-ranking
        """
        components = self._init_retrievers()
        hybrid_retriever = components["hybrid_retriever"]
        dense_retriever = components["dense_retriever"]
        lexical_retriever = components["lexical_retriever"]
        query_analyzer = components["query_analyzer"]
        deterministic_reranker = components["deterministic_reranker"]
        passthrough_reranker = components["passthrough_reranker"]

        # Build retrievers for each ablation configuration
        configs = {
            "dense_only": dense_retriever,
            "bm25_only": lexical_retriever,
            "hybrid_rrf": hybrid_retriever,
            "hybrid_plus_filter": EnhancedRetriever(
                hybrid_retriever=hybrid_retriever,
                reranker=passthrough_reranker,
                query_analyzer=query_analyzer,
                metadata_filter=MetadataFilter(mode="soft"),
                candidate_k=20,
                filter_mode="soft",
                enable_query_analysis=True,
                enable_reranking=False,
            ),
            "hybrid_plus_rerank": EnhancedRetriever(
                hybrid_retriever=hybrid_retriever,
                reranker=deterministic_reranker,
                query_analyzer=query_analyzer,
                metadata_filter=MetadataFilter(mode="soft"),
                candidate_k=20,
                filter_mode="soft",
                enable_query_analysis=False,
                enable_reranking=True,
            ),
            "hybrid_filter_rerank": EnhancedRetriever(
                hybrid_retriever=hybrid_retriever,
                reranker=deterministic_reranker,
                query_analyzer=query_analyzer,
                metadata_filter=MetadataFilter(mode="soft"),
                candidate_k=20,
                filter_mode="soft",
                enable_query_analysis=True,
                enable_reranking=True,
            ),
        }

        ablation_results: dict[str, Any] = {}

        for config_name, retriever in configs.items():
            config_metrics_by_k: dict[str, Any] = {}

            for k in self.top_k_values:
                recalls_at_1 = []
                recalls_at_3 = []
                recalls_at_5 = []
                reciprocal_ranks = []
                latencies_ms = []

                for query_item in self.dataset:
                    # Execute multiple runs to measure realistic latency statistics
                    query_latencies = []
                    results = []
                    for _ in range(num_runs_per_query):
                        t0 = time.perf_counter()
                        results = retriever.search(query=query_item.query, top_k=k)
                        query_latencies.append((time.perf_counter() - t0) * 1000.0)

                    latencies_ms.extend(query_latencies)

                    # Compute retrieval quality metrics
                    retrieved_ids = [getattr(r, "chunk_id", "") for r in results]
                    expected_set = set(query_item.expected_chunk_ids)

                    # Recall@1
                    hit_at_1 = 1.0 if retrieved_ids and retrieved_ids[0] in expected_set else 0.0
                    recalls_at_1.append(hit_at_1)

                    # Recall@3
                    hit_at_3 = 1.0 if any(cid in expected_set for cid in retrieved_ids[:3]) else 0.0
                    recalls_at_3.append(hit_at_3)

                    # Recall@5
                    hit_at_5 = 1.0 if any(cid in expected_set for cid in retrieved_ids[:5]) else 0.0
                    recalls_at_5.append(hit_at_5)

                    # MRR
                    rr = 0.0
                    for rank_idx, cid in enumerate(retrieved_ids, start=1):
                        if cid in expected_set:
                            rr = 1.0 / rank_idx
                            break
                    reciprocal_ranks.append(rr)

                # Aggregate metrics for this K
                mean_lat = statistics.mean(latencies_ms)
                median_lat = statistics.median(latencies_ms)
                p95_lat = (
                    sorted(latencies_ms)[int(0.95 * len(latencies_ms))]
                    if len(latencies_ms) > 1
                    else mean_lat
                )

                config_metrics_by_k[f"k_{k}"] = {
                    "k": k,
                    "recall_at_1": round(statistics.mean(recalls_at_1), 4),
                    "recall_at_3": round(statistics.mean(recalls_at_3), 4),
                    "recall_at_5": round(statistics.mean(recalls_at_5), 4),
                    "mrr": round(statistics.mean(reciprocal_ranks), 4),
                    "latency_ms": {
                        "mean": round(mean_lat, 2),
                        "median": round(median_lat, 2),
                        "p95": round(p95_lat, 2),
                    },
                }

            ablation_results[config_name] = config_metrics_by_k

        # Category breakdown for default Top-K=5
        category_breakdown: dict[str, dict[str, float]] = {}
        for query_item in self.dataset:
            cat = query_item.category
            if cat not in category_breakdown:
                category_breakdown[cat] = {}
            for config_name, retriever in configs.items():
                results = retriever.search(query=query_item.query, top_k=5)
                retrieved_ids = [getattr(r, "chunk_id", "") for r in results]
                hit = 1.0 if any(cid in set(query_item.expected_chunk_ids) for cid in retrieved_ids) else 0.0
                category_breakdown[cat][config_name] = hit

        return {
            "dataset_version": self.DATASET_VERSION,
            "dataset_hash": self.dataset_hash,
            "dataset_query_count": len(self.dataset),
            "timestamp": datetime.now(UTC).isoformat(),
            "top_k_values": list(self.top_k_values),
            "ablations": ablation_results,
            "category_breakdown": category_breakdown,
        }

    def save_results(self, results: dict[str, Any], output_path: Path | str) -> None:
        """Serialize benchmark results to a machine-readable JSON file."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
