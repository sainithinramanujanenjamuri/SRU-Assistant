"""Data models and exceptions for vector storage, embedding manifest, and retrieval."""
from __future__ import annotations



from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from typing import Any


from pydantic import BaseModel, Field, model_validator

# ==============================================================================
# Exceptions
# ==============================================================================


class RetrievalError(Exception):
    """Base exception for all retrieval operations."""


class IndexCompatibilityError(RetrievalError):
    """Raised when an embedding configuration is incompatible with the existing index manifest."""


class EmbeddingError(RetrievalError):
    """Raised when an embedding provider fails to generate vectors."""


class EmbeddingProviderUnavailableError(EmbeddingError):
    """Raised when a requested embedding backend service (e.g. Ollama daemon) is unavailable."""


class VectorStoreError(RetrievalError):
    """Raised when a vector store operation fails."""


class BM25Error(RetrievalError):
    """Base exception for BM25 lexical retrieval operations."""


class BM25IndexError(BM25Error):
    """Raised when an operation on the BM25 inverted index fails or index is missing."""


class BM25CorruptionError(BM25Error):
    """Raised when a persistent BM25 index file is corrupted or unreadable."""


class RerankerError(RetrievalError):
    """Base exception for all re-ranking operations."""


class RerankerUnavailableError(RerankerError):
    """Raised when a requested re-ranking provider (e.g. sentence-transformers or Ollama) is unavailable."""


class FilterError(RetrievalError):
    """Raised when metadata filtering fails due to invalid parameters or corrupted metadata."""


# ==============================================================================
# Domain Models
# ==============================================================================


class IndexManifest(BaseModel):
    """Metadata describing the identity, embedding model, and schema of a vector index.

    Stored alongside the vector index to prevent silent corruption or mixing of
    incompatible embedding vectors.
    """

    embedding_provider: str = Field(
        ..., description="Embedding provider name (e.g. 'fasthash', 'ollama', 'sentence_transformers')"
    )
    embedding_model: str = Field(..., description="Embedding model identifier (e.g. 'fasthash-384', 'nomic-embed-text')")
    embedding_dimension: int = Field(..., gt=0, description="Dimensionality of vectors stored in the index")
    distance_metric: str = Field(default="cosine", description="Distance/similarity metric (default: 'cosine')")
    index_version: str = Field(default="1.0.0", description="Index schema version")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp of index initialization",
    )
    total_vectors: int = Field(default=0, ge=0, description="Total number of vector records in the index")

    def is_compatible_with(self, provider: str, model: str, dimension: int) -> tuple[bool, str]:
        """Validate if a candidate query embedding setup is compatible with this index.

        Returns (is_compatible, reason).
        """
        if self.embedding_dimension != dimension:
            return (
                False,
                f"Dimension mismatch: index expects {self.embedding_dimension}-d vectors, "
                f"but query model produces {dimension}-d vectors. Re-indexing is required.",
            )
        if self.embedding_provider != provider or self.embedding_model != model:
            return (
                False,
                f"Model mismatch: index was built with '{self.embedding_provider}/{self.embedding_model}', "
                f"but query uses '{provider}/{model}'. Re-indexing is required to prevent corrupted rankings.",
            )
        return True, "Compatible"


class VectorRecord(BaseModel):
    """Full record stored in the vector database with complete traceability to the source chunk."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Canonical SHA-256 document identifier")
    text: str = Field(..., description="Full text content of the chunk")
    chunk_content_hash: str = Field(..., description="SHA-256 hash of the chunk text for stale detection")
    vector: list[float] = Field(..., description="Unit-normalized embedding vector")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Extracted metadata fields")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Traceable document provenance")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 creation timestamp",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 last-update timestamp",
    )


class VectorSearchResult(BaseModel):
    """Result of a semantic vector similarity search.

    Cosine similarity for unit-normalized vectors:
        cosine_similarity = dot(q, d) in [-1.0, 1.0]

    Min-max normalized score:
        normalized_score = (cosine_similarity + 1.0) / 2.0 in [0.0, 1.0]
    """

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Canonical SHA-256 document identifier")
    text: str = Field(..., description="Chunk text content")
    cosine_similarity: float = Field(..., description="Raw cosine similarity score in [-1.0, 1.0]")
    normalized_score: float = Field(..., ge=0.0, le=1.0, description="Normalized score in [0.0, 1.0]")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Preserved chunk metadata")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Preserved provenance breadcrumbs")

    @property
    def score(self) -> float:
        """Alias returning normalized_score for downstream RAG consumption."""
        return self.normalized_score

    @model_validator(mode="before")
    @classmethod
    def calculate_normalized_score(cls, data: Any) -> Any:
        """Ensure normalized_score is accurately computed from cosine_similarity if omitted."""
        if isinstance(data, dict):
            cos = data.get("cosine_similarity")
            if cos is not None and "normalized_score" not in data:
                # Clamp raw cosine to [-1.0, 1.0] to protect against slight floating point overshoot
                clamped_cos = max(-1.0, min(1.0, float(cos)))
                data["normalized_score"] = round((clamped_cos + 1.0) / 2.0, 6)
        return data


class IndexingReport(BaseModel):
    """Audit report produced by the VectorIndexer upon completing an indexing run."""

    chunks_requested: int = Field(default=0, ge=0, description="Total chunks submitted for indexing")
    chunks_indexed: int = Field(default=0, ge=0, description="New chunks embedded and added")
    chunks_updated: int = Field(default=0, ge=0, description="Existing chunks whose changed text was re-embedded")
    chunks_skipped: int = Field(default=0, ge=0, description="Existing unchanged chunks skipped (idempotent)")
    chunks_failed: int = Field(default=0, ge=0, description="Chunks that failed embedding or storage")
    elapsed_seconds: float = Field(default=0.0, ge=0.0, description="Total wall-clock duration of indexing run")
    manifest: IndexManifest | None = Field(default=None, description="Current manifest of the target index")


class BM25IndexManifest(BaseModel):
    """Metadata describing the identity, parameters, and schema of a BM25 inverted index."""

    index_version: str = Field(default="1.0.0", description="Index schema version")
    tokenizer_version: str = Field(default="1.0.0", description="Tokenizer version used for indexing")
    vocabulary_size: int = Field(..., ge=0, description="Total unique terms in the vocabulary")
    total_chunks: int = Field(..., ge=0, description="Total document chunks indexed")
    average_document_length: float = Field(..., ge=0.0, description="Average token length across chunks (avgdl)")
    k1: float = Field(default=1.5, gt=0.0, description="BM25 term frequency saturation parameter")
    b: float = Field(default=0.75, ge=0.0, le=1.0, description="BM25 document length normalization parameter")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="ISO 8601 UTC timestamp of index generation",
    )
    source_content_hash: str = Field(default="", description="Aggregated SHA-256 hash of all indexed chunk contents")

    def is_compatible_with(self, tokenizer_version: str, k1: float, b: float) -> tuple[bool, str]:
        """Check if candidate query settings match this index manifest."""
        if self.tokenizer_version != tokenizer_version:
            return (
                False,
                f"Tokenizer version mismatch: index was built with '{self.tokenizer_version}', "
                f"but current tokenizer is '{tokenizer_version}'. Re-indexing required.",
            )
        if abs(self.k1 - k1) > 1e-4 or abs(self.b - b) > 1e-4:
            return (
                False,
                f"BM25 parameter mismatch: index was built with k1={self.k1}, b={self.b}, "
                f"but current configuration specifies k1={k1}, b={b}. Re-indexing required.",
            )
        return True, "Compatible"


class LexicalSearchResult(BaseModel):
    """Result of a BM25 lexical keyword search.

    Exposes raw BM25 score, normalized score in [0.0, 1.0], rank, and preserved metadata.
    Note: min-max normalization is a per-query heuristic for fusion, not universally calibrated.
    """

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Canonical SHA-256 document identifier")
    text: str = Field(..., description="Chunk text content")
    bm25_score: float = Field(..., ge=0.0, description="Raw BM25 score")
    normalized_score: float = Field(..., ge=0.0, le=1.0, description="Per-query min-max normalized score in [0.0, 1.0]")
    rank: int = Field(..., ge=1, description="1-indexed rank in lexical candidate list")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Preserved chunk metadata")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Preserved provenance breadcrumbs")

    @property
    def score(self) -> float:
        """Alias returning normalized_score for downstream RAG consumption."""
        return self.normalized_score


class HybridSearchResult(BaseModel):
    """Unified search result produced by hybrid fusion (RRF or Weighted).

    Contains fused score, modality rankings, and original chunk data.
    """

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Canonical SHA-256 document identifier")
    text: str = Field(..., description="Chunk text content")
    fused_score: float = Field(..., ge=0.0, description="Fused score (RRF score or weighted combination)")
    normalized_fused_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Normalized fused score in [0.0, 1.0]"
    )
    dense_score: float | None = Field(default=None, description="Normalized dense retrieval score if present")
    dense_rank: int | None = Field(default=None, ge=1, description="1-indexed dense rank if present")
    lexical_score: float | None = Field(default=None, description="Normalized lexical retrieval score if present")
    lexical_rank: int | None = Field(default=None, ge=1, description="1-indexed lexical rank if present")
    fusion_method: str = Field(default="rrf", description="Fusion method used: 'rrf' or 'weighted'")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Preserved chunk metadata")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Preserved provenance breadcrumbs")

    @property
    def score(self) -> float:
        """Alias returning normalized_fused_score for downstream RAG consumption."""
        return self.normalized_fused_score

    @property
    def normalized_score(self) -> float:
        """Alias returning normalized_fused_score."""
        return self.normalized_fused_score


class HybridRetrievalMeta(BaseModel):
    """Observability diagnostics recorded for a hybrid retrieval query."""

    requested_mode: str = Field(..., description="Requested retrieval mode ('hybrid', 'dense', 'lexical')")
    actual_mode: str = Field(..., description="Actual executed mode ('hybrid', 'dense', 'lexical', 'dense_fallback', etc.)")
    fusion_method: str = Field(default="rrf", description="Fusion algorithm used")
    dense_candidates_retrieved: int = Field(default=0, ge=0)
    lexical_candidates_retrieved: int = Field(default=0, ge=0)
    fused_candidates_count: int = Field(default=0, ge=0)
    dense_latency_ms: float = Field(default=0.0, ge=0.0)
    lexical_latency_ms: float = Field(default=0.0, ge=0.0)
    fusion_latency_ms: float = Field(default=0.0, ge=0.0)
    total_retrieval_latency_ms: float = Field(default=0.0, ge=0.0)


class BM25IndexingReport(BaseModel):
    """Audit report produced by the BM25Indexer upon completing an indexing run."""

    chunks_requested: int = Field(default=0, ge=0)
    chunks_indexed: int = Field(default=0, ge=0)
    chunks_updated: int = Field(default=0, ge=0)
    chunks_skipped: int = Field(default=0, ge=0)
    chunks_removed: int = Field(default=0, ge=0)
    elapsed_seconds: float = Field(default=0.0, ge=0.0)
    manifest: BM25IndexManifest | None = Field(default=None)


class QueryAnalysisResult(BaseModel):
    """Structured extraction of academic entities and intent from student query.

    Produced by AcademicQueryAnalyzer in a deterministic, non-destructive manner.
    Provides suggested filters and intent classification without imposing hard exclusions.
    """

    query: str = Field(..., description="Original user query string")
    department: str | None = Field(default=None, description="Extracted department name/code if present")
    program: str | None = Field(default=None, description="Extracted degree program if present")
    semester: str | None = Field(default=None, description="Extracted academic semester if present")
    academic_year: str | None = Field(default=None, description="Extracted academic session year if present")
    document_type: str | None = Field(default=None, description="Inferred document type if present")
    course_code: str | None = Field(default=None, description="Extracted course code if present")
    regulation: str | None = Field(default=None, description="Extracted regulation code if present")
    question_type: str = Field(default="general", description="Classified intent category")
    dates: list[str] = Field(default_factory=list, description="Extracted date expressions")
    examination_terms: list[str] = Field(default_factory=list, description="Extracted examination terms")
    detected_entities: dict[str, Any] = Field(default_factory=dict, description="Consolidated dictionary of entities")
    suggested_filters: dict[str, Any] = Field(default_factory=dict, description="Recommended metadata constraints")
    normalized_values: dict[str, str] = Field(default_factory=dict, description="Canonical normalized representations")
    expanded_query: str | None = Field(default=None, description="Canonically expanded query with academic terminology")


class RerankResult(BaseModel):

    """Result of cross-feature or neural re-ranking over candidate evidence.

    Preserves full retrieval provenance, previous ranks and scores, and exposes
    explicit reranker provider and model identity.
    """

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Canonical SHA-256 document identifier")
    text: str = Field(..., description="Chunk text content")
    rerank_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Normalized relevance/ranking score in [0.0, 1.0] (heuristic or model-derived, NOT a probability)",
    )
    initial_score: float = Field(..., description="Pre-reranking candidate score (hybrid, dense, or lexical)")
    initial_rank: int = Field(..., ge=1, description="1-indexed rank prior to reranking")
    rerank_rank: int = Field(..., ge=1, description="1-indexed rank after reranking")
    rank_delta: int = Field(
        default=0,
        description="Rank movement: initial_rank - rerank_rank (positive = moved up, negative = moved down)",
    )
    reranker_name: str = Field(default="deterministic", description="Identifier of the reranker used")
    reranker_provider: str = Field(
        default="deterministic",
        description="Provider backend ('deterministic', 'sentence-transformers', 'ollama', 'passthrough')",
    )
    reranker_model: str = Field(default="deterministic-cross-feature-v1", description="Model or algorithm version used")
    dense_score: float | None = Field(default=None, description="Original normalized dense score if available")
    dense_rank: int | None = Field(default=None, ge=1, description="Original dense rank if available")
    lexical_score: float | None = Field(default=None, description="Original normalized lexical score if available")
    lexical_rank: int | None = Field(default=None, ge=1, description="Original lexical rank if available")
    initial_hybrid_rank: int | None = Field(default=None, ge=1, description="Original hybrid candidate rank")
    original_retrieval_mode: str = Field(default="hybrid", description="Retrieval mode that generated initial candidate")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Preserved chunk metadata")
    provenance: dict[str, Any] = Field(default_factory=dict, description="Preserved provenance breadcrumbs")

    @property
    def score(self) -> float:
        """Alias returning rerank_score for downstream RAG consumption."""
        return self.rerank_score

    @property
    def normalized_score(self) -> float:
        """Alias returning rerank_score."""
        return self.rerank_score


# Alias for backward/spec compatibility
RerankedSearchResult = RerankResult


class EnhancedRetrievalMeta(BaseModel):
    """Observability diagnostics recorded for an enhanced retrieval execution."""

    query_analysis_latency_ms: float = Field(default=0.0, ge=0.0)
    candidate_retrieval_latency_ms: float = Field(default=0.0, ge=0.0)
    metadata_filter_latency_ms: float = Field(default=0.0, ge=0.0)
    reranking_latency_ms: float = Field(default=0.0, ge=0.0)
    total_retrieval_latency_ms: float = Field(default=0.0, ge=0.0)
    initial_candidate_count: int = Field(default=0, ge=0)
    post_filter_count: int = Field(default=0, ge=0)
    final_count: int = Field(default=0, ge=0)
    moved_up_count: int = Field(default=0, ge=0)
    moved_down_count: int = Field(default=0, ge=0)
    unchanged_count: int = Field(default=0, ge=0)
    entered_top_k_count: int = Field(default=0, ge=0)
    left_top_k_count: int = Field(default=0, ge=0)
    retrieval_mode: str = Field(default="hybrid")
    filter_mode: str = Field(default="soft")
    reranker_name: str = Field(default="deterministic")
    reranker_provider: str = Field(default="deterministic")
    reranker_model: str = Field(default="deterministic-cross-feature-v1")
    query_analysis_result: QueryAnalysisResult | None = Field(default=None)
