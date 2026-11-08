"""Integration tests for RAGEvaluator and comparative experiment execution."""

from pathlib import Path
import pytest

from evaluation.datasets.benchmark_loader import BenchmarkDatasetLoader
from evaluation.evaluator import RAGEvaluator
from evaluation.generation.evaluator import GenerationEvaluator
from evaluation.models import BenchmarkQuery
from evaluation.reports.report_generator import ReportGenerator
from evaluation.retrieval.evaluator import RetrieverEvaluator


def test_retriever_evaluator():
    """Test RetrieverEvaluator over sample queries."""
    evaluator_env = RAGEvaluator()
    retriever = evaluator_env.dense_retriever

    evaluator = RetrieverEvaluator(k_values=(1, 3, 5))
    loader = BenchmarkDatasetLoader()
    sample_queries = loader.queries[:3]

    aggregate, per_query = evaluator.evaluate_dataset(retriever, sample_queries, top_k=5)
    assert aggregate.mrr >= 0.0
    assert 5 in aggregate.recall_at_k
    assert len(per_query) == 3


def test_rag_evaluator_experiment_run(tmp_path):
    """Test RAGEvaluator executing Experiment A and D with deterministic generator."""
    loader = BenchmarkDatasetLoader()
    # Test on a slice of queries to keep test fast
    test_queries = [
        loader.queries[0],  # direct factual
        loader.get_unanswerable_queries()[0],  # out of KB
    ]

    evaluator = RAGEvaluator(loader=loader)
    exp_d = evaluator.evaluate_experiment(
        exp_key="D",
        queries=test_queries,
        top_k=3,
        generator_provider="deterministic",
    )

    assert exp_d.experiment_id == "D"
    assert exp_d.total_queries == 2
    assert 0.0 <= exp_d.aggregate_generation.groundedness <= 1.0
    assert "total" in exp_d.aggregate_latency_ms

    # Test report generation
    report = evaluator.run_all_experiments(
        experiment_keys=("A", "D"),
        queries=test_queries,
        top_k=3,
        generator_provider="deterministic",
    )
    assert len(report.experiments) == 2

    reporter = ReportGenerator()
    json_path = tmp_path / "test_report.json"
    md_path = tmp_path / "test_report.md"

    reporter.save_json(report, json_path)
    assert json_path.exists()

    reporter.save_markdown(report, md_path)
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "Executive Summary" in content
    assert "Experiment A" in content
    assert "Experiment D" in content
