"""SRU Assistant - Evaluation package (retrieval, generation, RAG Triad, citation metrics, benchmarks, and reports)."""

from typing import Any

__all__ = [
    "BenchmarkQuery",
    "RetrievalMetrics",
    "GenerationMetrics",
    "CitationMetrics",
    "LatencyBreakdown",
    "QueryEvaluationResult",
    "ExperimentRunResult",
    "EvaluationReport",
    "BenchmarkDatasetLoader",
    "RetrieverEvaluator",
    "GenerationEvaluator",
    "RAGEvaluator",
    "ReportGenerator",
]


def __getattr__(name: str) -> Any:
    if name in (
        "BenchmarkQuery",
        "RetrievalMetrics",
        "GenerationMetrics",
        "CitationMetrics",
        "LatencyBreakdown",
        "QueryEvaluationResult",
        "ExperimentRunResult",
        "EvaluationReport",
    ):
        from evaluation import models
        return getattr(models, name)
    if name == "BenchmarkDatasetLoader":
        from evaluation.datasets.benchmark_loader import BenchmarkDatasetLoader
        return BenchmarkDatasetLoader
    if name == "RetrieverEvaluator":
        from evaluation.retrieval.evaluator import RetrieverEvaluator
        return RetrieverEvaluator
    if name == "GenerationEvaluator":
        from evaluation.generation.evaluator import GenerationEvaluator
        return GenerationEvaluator
    if name == "RAGEvaluator":
        from evaluation.evaluator import RAGEvaluator
        return RAGEvaluator
    if name == "ReportGenerator":
        from evaluation.reports.report_generator import ReportGenerator
        return ReportGenerator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
