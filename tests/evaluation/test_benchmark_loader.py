"""Unit tests for BenchmarkDatasetLoader and dataset consistency."""

from pathlib import Path
import pytest

from evaluation.datasets.benchmark_loader import BenchmarkDatasetLoader
from evaluation.models import CANONICAL_BENCHMARK_CATEGORIES


def test_benchmark_loader_default():
    """Test loading canonical benchmark suite."""
    loader = BenchmarkDatasetLoader()
    assert loader.total_queries > 0
    assert loader.dataset_version == "1.0.0"
    assert len(loader.dataset_hash) == 64  # SHA-256 length


def test_benchmark_loader_category_coverage():
    """Verify that all 10 canonical categories are covered in the dataset."""
    loader = BenchmarkDatasetLoader()
    dist = loader.get_category_distribution()

    for cat in CANONICAL_BENCHMARK_CATEGORIES:
        assert cat in dist
        assert dist[cat] > 0, f"Category '{cat}' has 0 queries in benchmark dataset"


def test_benchmark_loader_answerability():
    """Verify answerable vs unanswerable query filtering."""
    loader = BenchmarkDatasetLoader()
    answerable = loader.get_answerable_queries()
    unanswerable = loader.get_unanswerable_queries()

    assert len(answerable) + len(unanswerable) == loader.total_queries
    assert len(unanswerable) >= 2  # At least out-of-KB test queries


def test_benchmark_loader_missing_file():
    """Test error handling when dataset file is missing."""
    with pytest.raises(FileNotFoundError):
        BenchmarkDatasetLoader(dataset_path=Path("non_existent_path.json"))
