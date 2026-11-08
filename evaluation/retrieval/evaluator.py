"""Retriever evaluation runner for the SRU Assistant benchmark."""

import statistics
import time
from typing import Sequence

from evaluation.models import BenchmarkQuery, RetrievalMetrics
from evaluation.retrieval.metrics import (
    compute_mrr,
    compute_ndcg_at_k,
    compute_precision_at_k,
    compute_recall_at_k,
)
from retrieval.base import BaseRetriever


class RetrieverEvaluator:
    """Evaluates BaseRetriever implementations against benchmark queries."""

    def __init__(self, k_values: tuple[int, ...] = (1, 3, 5)):
        self.k_values = k_values

    def evaluate_query(
        self,
        retriever: BaseRetriever,
        query: BenchmarkQuery,
        top_k: int = 5,
    ) -> tuple[RetrievalMetrics, list[str]]:
        """Evaluate retrieval performance for a single benchmark query."""
        t0 = time.perf_counter()
        results = retriever.search(query=query.query, top_k=top_k)
        retrieval_ms = (time.perf_counter() - t0) * 1000.0

        retrieved_chunk_ids = [r.chunk_id for r in results]

        recall_dict = {
            k: compute_recall_at_k(retrieved_chunk_ids, query.expected_chunk_ids, k)
            for k in self.k_values
        }
        precision_dict = {
            k: compute_precision_at_k(retrieved_chunk_ids, query.expected_chunk_ids, k)
            for k in self.k_values
        }
        mrr = compute_mrr(retrieved_chunk_ids, query.expected_chunk_ids)
        ndcg_dict = {
            k: compute_ndcg_at_k(retrieved_chunk_ids, query.expected_chunk_ids, k)
            for k in (3, 5)
            if k in self.k_values
        }

        metrics = RetrievalMetrics(
            recall_at_k=recall_dict,
            precision_at_k=precision_dict,
            mrr=round(mrr, 4),
            ndcg_at_k=ndcg_dict,
            latency_ms={"mean": round(retrieval_ms, 2)},
        )
        return metrics, retrieved_chunk_ids

    def evaluate_dataset(
        self,
        retriever: BaseRetriever,
        queries: Sequence[BenchmarkQuery],
        top_k: int = 5,
    ) -> tuple[RetrievalMetrics, dict[str, tuple[RetrievalMetrics, list[str]]]]:
        """Evaluate retriever over a full benchmark dataset, computing macro-averages."""
        per_query: dict[str, tuple[RetrievalMetrics, list[str]]] = {}
        all_recalls: dict[int, list[float]] = {k: [] for k in self.k_values}
        all_precisions: dict[int, list[float]] = {k: [] for k in self.k_values}
        all_mrr: list[float] = []
        all_ndcg: dict[int, list[float]] = {k: [] for k in (3, 5) if k in self.k_values}
        all_latencies: list[float] = []

        for q in queries:
            m, retrieved_ids = self.evaluate_query(retriever, q, top_k=top_k)
            per_query[q.query_id] = (m, retrieved_ids)

            for k in self.k_values:
                all_recalls[k].append(m.recall_at_k.get(k, 0.0))
                all_precisions[k].append(m.precision_at_k.get(k, 0.0))
            all_mrr.append(m.mrr)
            for k in all_ndcg:
                all_ndcg[k].append(m.ndcg_at_k.get(k, 0.0))
            all_latencies.append(m.latency_ms.get("mean", 0.0))

        count = len(queries)
        if count == 0:
            return RetrievalMetrics(), per_query

        macro_recall = {k: round(sum(vals) / count, 4) for k, vals in all_recalls.items()}
        macro_precision = {k: round(sum(vals) / count, 4) for k, vals in all_precisions.items()}
        macro_mrr = round(sum(all_mrr) / count, 4)
        macro_ndcg = {k: round(sum(vals) / count, 4) for k, vals in all_ndcg.items()}

        mean_lat = round(statistics.mean(all_latencies), 2) if all_latencies else 0.0
        med_lat = round(statistics.median(all_latencies), 2) if all_latencies else 0.0
        p95_lat = (
            round(sorted(all_latencies)[int(0.95 * len(all_latencies))], 2)
            if all_latencies
            else 0.0
        )

        aggregate = RetrievalMetrics(
            recall_at_k=macro_recall,
            precision_at_k=macro_precision,
            mrr=macro_mrr,
            ndcg_at_k=macro_ndcg,
            latency_ms={"mean": mean_lat, "median": med_lat, "p95": p95_lat},
        )
        return aggregate, per_query
