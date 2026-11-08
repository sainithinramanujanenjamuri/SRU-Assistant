"""Data models for SRU Assistant quantitative RAG Evaluation (Phase 9).

Defines structured entities for benchmark queries, retrieval metrics,
generation metrics (RAG Triad), citation metrics, and multi-experiment reports.
"""
from __future__ import annotations



from typing import Any
from pydantic import BaseModel, ConfigDict, Field, field_validator


CANONICAL_BENCHMARK_CATEGORIES: tuple[str, ...] = (
    "direct_factual",
    "date_based",
    "course_related",
    "regulation",
    "department_specific",
    "multi_document",
    "paraphrased",
    "ambiguous",
    "out_of_knowledge_base",
    "version_sensitive",
)


class BenchmarkQuery(BaseModel):
    """Specification of an academic evaluation query with associated ground-truth provenance."""

    model_config = ConfigDict(frozen=True)

    query_id: str
    query: str
    category: str
    expected_answer: str
    expected_chunk_ids: list[str] = Field(default_factory=list)
    expected_document_names: list[str] = Field(default_factory=list)
    expected_pages: list[int | None] = Field(default_factory=list)
    expected_entities: list[str] = Field(default_factory=list)
    expected_behavior: str = "answer"  # "answer" | "insufficient_evidence"
    is_answerable: bool = True
    description: str = ""

    @field_validator("category")
    @classmethod
    def validate_category(cls, val: str) -> str:
        cleaned = val.strip().lower()
        if cleaned not in CANONICAL_BENCHMARK_CATEGORIES:
            raise ValueError(
                f"Unknown benchmark category '{val}'. Expected one of: "
                f"{', '.join(CANONICAL_BENCHMARK_CATEGORIES)}"
            )
        return cleaned

    @field_validator("query_id", "query")
    @classmethod
    def validate_non_empty(cls, val: str) -> str:
        if not val or not val.strip():
            raise ValueError("Field cannot be empty or whitespace-only")
        return val.strip()


class RetrievalMetrics(BaseModel):
    """Quantitative evaluation metrics for information retrieval."""

    model_config = ConfigDict(frozen=True)

    recall_at_k: dict[int, float] = Field(default_factory=dict)
    precision_at_k: dict[int, float] = Field(default_factory=dict)
    mrr: float = 0.0
    ndcg_at_k: dict[int, float] = Field(default_factory=dict)
    latency_ms: dict[str, float] = Field(default_factory=dict)

    @field_validator("mrr")
    @classmethod
    def validate_mrr_range(cls, val: float) -> float:
        if not (0.0 <= val <= 1.0001):
            raise ValueError(f"MRR must be in [0.0, 1.0], got {val}")
        return max(0.0, min(1.0, val))


class GenerationMetrics(BaseModel):
    """Quantitative evaluation metrics for answer generation including RAG Triad."""

    model_config = ConfigDict(frozen=True)

    groundedness: float = 0.0  # RAG Triad 1: Faithfulness to context
    answer_relevance: float = 0.0  # RAG Triad 2: Alignment to query
    context_relevance: float = 0.0  # RAG Triad 3: Context quality/conciseness
    correctness: float = 0.0  # Factual / token agreement with expected answer
    completeness: float = 0.0  # Coverage of required expected entities
    unsupported_claim_rate: float = 0.0  # 1.0 - groundedness

    @field_validator(
        "groundedness",
        "answer_relevance",
        "context_relevance",
        "correctness",
        "completeness",
        "unsupported_claim_rate",
    )
    @classmethod
    def validate_unit_interval(cls, val: float) -> float:
        if not (-0.0001 <= val <= 1.0001):
            raise ValueError(f"Metric score must be within [0.0, 1.0], got {val}")
        return max(0.0, min(1.0, val))


class CitationMetrics(BaseModel):
    """Quantitative evaluation metrics for source attribution and verification."""

    model_config = ConfigDict(frozen=True)

    citation_precision: float = 0.0
    citation_recall: float = 0.0
    citation_completeness: float = 0.0
    evidence_support: float = 0.0

    @field_validator(
        "citation_precision",
        "citation_recall",
        "citation_completeness",
        "evidence_support",
    )
    @classmethod
    def validate_unit_interval(cls, val: float) -> float:
        if not (-0.0001 <= val <= 1.0001):
            raise ValueError(f"Metric score must be within [0.0, 1.0], got {val}")
        return max(0.0, min(1.0, val))


class LatencyBreakdown(BaseModel):
    """Empirical runtime latency profile decomposed by RAG pipeline stage."""

    model_config = ConfigDict(frozen=True)

    retrieval_ms: float = 0.0
    context_ms: float = 0.0
    conflict_ms: float = 0.0
    generation_ms: float = 0.0
    grounding_ms: float = 0.0
    citation_ms: float = 0.0
    total_ms: float = 0.0


class QueryEvaluationResult(BaseModel):
    """Complete evaluation record for an individual benchmark query."""

    model_config = ConfigDict(frozen=True)

    query_id: str
    query: str
    category: str
    is_answerable: bool
    expected_behavior: str
    actual_answer: str
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    retrieval_metrics: RetrievalMetrics
    generation_metrics: GenerationMetrics
    citation_metrics: CitationMetrics
    latency: LatencyBreakdown
    passed_grounding: bool = True
    passed_verification: bool = True


class ExperimentRunResult(BaseModel):
    """Aggregate benchmark results for an entire experimental configuration."""

    model_config = ConfigDict(frozen=True)

    experiment_id: str
    name: str
    description: str
    retrieval_mode: str
    reranking_enabled: bool
    grounding_validation_enabled: bool
    citation_verification_enabled: bool
    total_queries: int
    aggregate_retrieval: RetrievalMetrics
    aggregate_generation: GenerationMetrics
    aggregate_citation: CitationMetrics
    aggregate_latency_ms: dict[str, dict[str, float]] = Field(default_factory=dict)
    category_metrics: dict[str, dict[str, Any]] = Field(default_factory=dict)
    query_results: list[QueryEvaluationResult] = Field(default_factory=list)


class EvaluationReport(BaseModel):
    """Multi-experiment comparative report artifact across the benchmark suite."""

    model_config = ConfigDict(frozen=True)

    report_id: str
    generated_at: str
    dataset_version: str
    dataset_hash: str
    total_queries: int
    category_distribution: dict[str, int]
    experiments: dict[str, ExperimentRunResult]
