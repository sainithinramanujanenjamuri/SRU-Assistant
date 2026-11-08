"""Dataset loader and validator for the SRU Assistant evaluation suite."""
from __future__ import annotations


import hashlib
import json
from pathlib import Path
from typing import Sequence

from evaluation.models import BenchmarkQuery, CANONICAL_BENCHMARK_CATEGORIES

DEFAULT_BENCHMARK_PATH = Path("data/benchmarks/eval_benchmark_suite.json")


def compute_benchmark_hash(queries: Sequence[BenchmarkQuery]) -> str:
    """Compute deterministic SHA-256 hash over canonical representation of queries."""

    elements = []
    for q in queries:
        chunks_str = ",".join(sorted(q.expected_chunk_ids))
        entities_str = ",".join(sorted(q.expected_entities))
        elements.append(
            f"{q.query_id}:{q.category}:{q.is_answerable}:{q.query}:{chunks_str}:{entities_str}"
        )
    raw = "\n".join(elements)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class BenchmarkDatasetLoader:
    """Loads, validates, and slices evaluation benchmark queries."""

    def __init__(self, dataset_path: Path | str | None = None):
        self.path = Path(dataset_path) if dataset_path else DEFAULT_BENCHMARK_PATH
        self._raw_data: dict = {}
        self._queries: list[BenchmarkQuery] = []
        self._dataset_hash: str = ""
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            raise FileNotFoundError(f"Benchmark dataset file not found at: {self.path.resolve()}")

        with open(self.path, "r", encoding="utf-8") as f:
            self._raw_data = json.load(f)

        raw_queries = self._raw_data.get("queries", [])
        if not raw_queries:
            raise ValueError(f"No queries found in benchmark dataset at {self.path}")

        parsed_queries: list[BenchmarkQuery] = []
        for item in raw_queries:
            q = BenchmarkQuery(**item)
            parsed_queries.append(q)

        self._queries = parsed_queries
        self._dataset_hash = compute_benchmark_hash(self._queries)

    @property
    def queries(self) -> list[BenchmarkQuery]:
        """Return all loaded benchmark queries."""
        return list(self._queries)

    @property
    def dataset_version(self) -> str:
        """Return dataset version string."""
        return self._raw_data.get("version", "1.0.0")

    @property
    def dataset_hash(self) -> str:
        """Return deterministic SHA-256 hash of the query suite."""
        return self._dataset_hash

    @property
    def total_queries(self) -> int:
        """Return total number of queries."""
        return len(self._queries)

    def get_by_category(self, category: str) -> list[BenchmarkQuery]:
        """Filter benchmark queries by canonical category."""
        clean_cat = category.strip().lower()
        if clean_cat not in CANONICAL_BENCHMARK_CATEGORIES:
            raise ValueError(f"Unknown category '{category}'")
        return [q for q in self._queries if q.category == clean_cat]

    def get_category_distribution(self) -> dict[str, int]:
        """Return counts of queries per category."""
        dist = {cat: 0 for cat in CANONICAL_BENCHMARK_CATEGORIES}
        for q in self._queries:
            dist[q.category] = dist.get(q.category, 0) + 1
        return dist

    def get_answerable_queries(self) -> list[BenchmarkQuery]:
        """Return only in-knowledge-base queries."""
        return [q for q in self._queries if q.is_answerable]

    def get_unanswerable_queries(self) -> list[BenchmarkQuery]:
        """Return out-of-knowledge-base queries."""
        return [q for q in self._queries if not q.is_answerable]
