"""Configuration settings for SRU Assistant using Pydantic Settings."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Environment
    app_env: str = Field(default="development", description="Environment: development, staging, production")
    app_name: str = Field(default="SRU Assistant", description="Application name")
    debug: bool = Field(default=True, description="Debug mode flag")
    log_level: str = Field(default="INFO", description="Logging level")
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")

    @field_validator("debug", mode="before")
    @classmethod
    def parse_debug_flag(cls, v: object) -> bool:
        """Parse boolean debug flag tolerating common environment strings."""
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            clean = v.strip().lower()
            if clean in {"true", "1", "yes", "t", "dev", "development", "debug"}:
                return True
            if clean in {"false", "0", "no", "f", "prod", "production", "release"}:
                return False
        return bool(v)

    # Document Processing Directories & Ingestion Options
    raw_documents_dir: str = Field(default="./documents/raw", description="Path to raw institutional documents")
    processed_documents_dir: str = Field(default="./documents/processed", description="Path to processed documents")
    ingestion_supported_extensions: list[str] = Field(
        default=[".pdf", ".docx", ".txt"], description="List of supported file extensions"
    )
    ingestion_header_footer_threshold: float = Field(
        default=0.8, description="Page frequency ratio to consider repeated text as candidate header/footer"
    )
    ingestion_encoding_fallbacks: list[str] = Field(
        default=["utf-8", "utf-8-sig", "latin-1"], description="Fallback encodings for plain text loading"
    )

    # Chunking & Knowledge Preparation Configuration (Phase 2)
    chunk_target_tokens: int = Field(default=500, description="Target chunk size in tokens")
    chunk_overlap_tokens: int = Field(default=100, description="Token overlap between consecutive chunks")
    chunk_min_tokens: int = Field(default=50, description="Minimum tokens to avoid orphaned fragments")
    chunk_max_tokens: int = Field(default=1200, description="Upper bound token limit before forcing a split")
    chunks_dir: str = Field(default="./documents/chunks", description="Directory to store structured chunk datasets")

    # Vector Store Configuration (Phase 3)
    vectorstore_backend: str = Field(default="sqlite", description="Vector store backend: sqlite")
    vectorstore_path: str = Field(default="./data/vectorstore/sru_vectors.db", description="Local SQLite vector database path")
    vectorstore_manifest_path: str = Field(
        default="./data/vectorstore/index_manifest.json", description="Index manifest metadata file path"
    )
    vectorstore_collection_name: str = Field(
        default="sru_academic_docs", description="Vector store collection name"
    )

    # Embedding Configuration (Phase 3)
    embedding_provider: str = Field(
        default="fasthash",
        description="Embedding provider: fasthash (deterministic lexical baseline), ollama, sentence_transformers",
    )
    embedding_model: str = Field(default="fasthash-384", description="Embedding model identifier")
    embedding_dimension: int = Field(default=384, description="Embedding vector dimension")
    embedding_batch_size: int = Field(default=32, description="Batch size for vector embedding operations")
    embedding_ollama_base_url: str = Field(default="http://localhost:11434", description="Ollama API base URL")
    embedding_timeout_seconds: float = Field(default=30.0, description="Embedding request timeout in seconds")

    # Generator & LLM Configuration (Phase 4)
    llm_provider: str = Field(
        default="deterministic",
        description="Generator provider: deterministic (rule-based baseline), ollama, openai_compatible",
    )
    llm_model: str = Field(default="qwen3.5:0.8b", description="LLM model identifier")
    llm_api_base: str = Field(default="http://localhost:11434", description="LLM service base URL")
    llm_api_key: str = Field(default="", description="LLM API key (if required by provider)")
    llm_temperature: float = Field(default=0.0, description="Sampling temperature for grounded generation")
    llm_max_tokens: int = Field(default=512, description="Maximum tokens for generated response")
    llm_top_p: float | None = Field(default=None, description="Nucleus sampling parameter for LLM generation")
    llm_timeout_seconds: float = Field(default=60.0, description="Timeout for generator requests in seconds")
    llm_enable_thinking: bool = Field(
        default=False, description="Enable reasoning/thinking mode for thinking-capable models (e.g. Qwen3.5)"
    )
    llm_endpoint_mode: str = Field(
        default="chat", description="Ollama API endpoint mode: 'chat', 'generate', or 'auto'"
    )

    # Baseline RAG Parameters (Phase 4)
    rag_context_max_tokens: int = Field(
        default=1500, description="Maximum token budget for retrieved evidence context"
    )
    rag_relevance_threshold: float = Field(
        default=0.40,
        description="Initial development threshold for normalized retrieval score (subject to Phase 9 calibration)",
    )

    # Grounded Generation Configuration (Phase 7)
    grounding_validation_enabled: bool = Field(
        default=True, description="Enable post-generation grounding validation"
    )
    grounding_strict_mode: bool = Field(
        default=False,
        description="Strict grounding mode: enforce no-answer or safe remediation on ungrounded claims",
    )
    conflict_detection_enabled: bool = Field(
        default=True, description="Enable cross-document institutional conflict detection"
    )
    grounded_system_prompt_style: str = Field(
        default="default",
        description="Grounded system prompt style: 'default', 'academic_rigor', or 'concise'",
    )
    grounding_min_token_overlap: float = Field(
        default=0.4,
        description="Minimum token overlap threshold for statement-evidence support approximation",
    )

    @field_validator("grounded_system_prompt_style")
    @classmethod
    def validate_prompt_style(cls, v: str) -> str:
        allowed = {"default", "academic_rigor", "concise"}
        if v not in allowed:
            raise ValueError(f"grounded_system_prompt_style must be one of {allowed}, got '{v}'")
        return v

    # Citation & Provenance Configuration (Phase 8)
    citation_style: str = Field(
        default="inline_bracket",
        description="Citation rendering style: 'inline_bracket', 'source_block', or 'footnote'",
    )
    citation_verification_enabled: bool = Field(
        default=True,
        description="Enable deterministic claim-evidence citation verification",
    )
    citation_min_support_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum threshold for considering a citation factually supported",
    )
    citation_require_exact_entities: bool = Field(
        default=True,
        description="Enforce exact academic entity containment between claim and cited chunk",
    )

    @field_validator("citation_style")
    @classmethod
    def validate_citation_style(cls, v: str) -> str:
        allowed = {"inline_bracket", "source_block", "footnote"}
        if v not in allowed:
            raise ValueError(f"citation_style must be one of {allowed}, got '{v}'")
        return v

    # Retrieval Configuration
    retrieval_top_k: int = Field(default=5, description="Default number of document chunks to retrieve")
    retrieval_hybrid_enabled: bool = Field(default=True, description="Enable hybrid semantic + lexical search")
    retrieval_reranking_enabled: bool = Field(default=False, description="Enable re-ranking step (Phase 6)")

    # Retrieval Enhancement & Re-ranking Configuration (Phase 6)
    reranker_type: str = Field(
        default="deterministic",
        description="Reranker provider type: 'deterministic', 'transformer', 'ollama', or 'passthrough'",
    )
    reranker_model_name: str = Field(
        default="cross-encoder/ms-marco-MiniLM-L-6-v2",
        description="Model identifier for neural cross-encoder or Ollama reranker",
    )
    reranker_candidate_k: int = Field(
        default=20,
        description="Candidate pool size passed from hybrid retrieval to re-ranking",
    )
    retrieval_filter_mode: str = Field(
        default="soft",
        description="Metadata filtering mode: 'soft' (score adjustment) or 'hard' (eligibility pruning)",
    )
    query_analysis_enabled: bool = Field(
        default=True,
        description="Enable academic query analysis for intent and entity extraction",
    )
    allow_reranker_fallback: bool = Field(
        default=False,
        description="Whether to permit fallback to deterministic reranker if neural reranker fails",
    )
    soft_filter_boost: float = Field(
        default=0.15,
        description="Score bonus added for matching metadata constraints in soft filtering mode",
    )
    soft_filter_penalty: float = Field(
        default=0.15,
        description="Score penalty subtracted for non-global mismatching metadata in soft filtering mode",
    )

    # Hybrid Retrieval Configuration (Phase 5)
    retrieval_mode: str = Field(
        default="hybrid",
        description="Retrieval mode: 'hybrid' (dense + lexical), 'dense' (vector only), or 'lexical' (BM25 only)",
    )
    hybrid_fusion_method: str = Field(
        default="rrf",
        description="Fusion strategy: 'rrf' (Reciprocal Rank Fusion) or 'weighted' (score combination)",
    )
    hybrid_dense_candidate_k: int = Field(
        default=20,
        description="Candidate pool size retrieved from dense vector channel prior to fusion",
    )
    hybrid_lexical_candidate_k: int = Field(
        default=20,
        description="Candidate pool size retrieved from BM25 lexical channel prior to fusion",
    )
    hybrid_final_top_k: int = Field(
        default=5,
        description="Number of final fused candidates to return to context builder",
    )
    hybrid_rrf_k: int = Field(
        default=60,
        description="Smoothing constant k for Reciprocal Rank Fusion (standard default: 60)",
    )
    hybrid_dense_weight: float = Field(
        default=0.5,
        description="Weight assigned to dense modality in fusion (initial heuristic, evaluated in Phase 9)",
    )
    hybrid_lexical_weight: float = Field(
        default=0.5,
        description="Weight assigned to lexical modality in fusion (initial heuristic, evaluated in Phase 9)",
    )
    hybrid_allow_fallback: bool = Field(
        default=False,
        description="Whether to permit single-channel fallback if one retrieval channel fails",
    )

    # BM25 Lexical Configuration (Phase 5)
    bm25_k1: float = Field(
        default=1.5,
        description="BM25 term frequency saturation parameter k1 (standard range: 1.2 - 2.0)",
    )
    bm25_b: float = Field(
        default=0.75,
        description="BM25 document length normalization parameter b (standard default: 0.75)",
    )
    bm25_index_path: Path = Field(
        default=Path("data/indices/bm25_index.json"),
        description="Filesystem path to the persistent BM25 inverted index file",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached singleton instance of application settings."""
    return Settings()
