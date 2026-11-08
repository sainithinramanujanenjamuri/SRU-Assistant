"""Unit tests for embedding and retrieval benchmarking harness."""

from retrieval.embeddings.benchmark import (
    run_embedding_latency_benchmark,
    run_preliminary_retrieval_benchmark,
)
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel


class TestBenchmarking:
    """Test embedding benchmark runner and preliminary retrieval evaluation."""

    def test_latency_benchmark_metrics(self):
        model = FastHashEmbeddingModel(dimension=128)
        sample_texts = [
            "SR University Academic Regulations 2026-27",
            "Mid-Semester Examination Schedule for VII Semester B.Tech",
            "Department of Computer Science and Engineering",
        ]

        results = run_embedding_latency_benchmark(model, sample_texts, warmup_runs=1)

        assert results["provider"] == "fasthash"
        assert results["dimension"] == 128
        assert results["sample_count"] == 3
        assert results["single_avg_latency_ms"] >= 0.0
        assert results["batch_avg_latency_ms"] >= 0.0
        assert results["single_throughput_chunks_sec"] > 0.0
        assert results["max_l2_norm_error"] < 1e-4

    def test_preliminary_retrieval_benchmark_execution(self):
        model = FastHashEmbeddingModel(dimension=384)
        results = run_preliminary_retrieval_benchmark(model, k_values=(1, 3))

        assert results["provider"] == "fasthash"
        assert results["queries_evaluated"] == 4
        assert results["corpus_size"] == 4
        assert 0.0 <= results["mrr"] <= 1.0
        assert 0.0 <= results["Recall@1"] <= 1.0
        assert 0.0 <= results["Recall@3"] <= 1.0
