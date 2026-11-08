"""Pydantic schemas for the SRU Assistant API layer (Phase 10)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Student query request payload."""

    query: str = Field(..., min_length=2, max_length=1000, description="Academic question text")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of candidate chunks to retrieve")
    retrieval_mode: str = Field(default="enhanced", description="Retrieval mode: dense, lexical, hybrid, enhanced")
    verify_citations: bool = Field(default=True, description="Whether to execute claim-evidence verification")
    citation_style: str = Field(default="inline_bracket", description="Citation formatting style")


class CitationDetail(BaseModel):
    """Detailed attribution information for a cited claim."""

    citation_id: str
    document_name: str
    page: int | None
    page_info: str
    section: str
    source_label: str
    chunk_id: str
    claim_text: str | None = None
    is_verified: bool = True
    support_score: float | None = 1.0


class VerificationSummary(BaseModel):
    """Provenance and verification audit summary."""

    is_fully_supported: bool
    citation_precision: float
    citation_recall: float
    overall_support_score: float
    unsupported_claims_count: int = 0


class QueryResponse(BaseModel):
    """Complete academic response with grounded evidence and citations."""

    request_id: str = Field(default="", description="Unique tracking identifier for request lifecycle")
    query: str
    answer: str
    cited_answer: str
    citations: list[CitationDetail]
    verification: VerificationSummary
    is_grounded: bool
    has_conflicts: bool
    conflict_notes: list[str] = Field(default_factory=list)
    latency_ms: dict[str, float]
    engine_info: dict[str, Any]


class DocumentSummary(BaseModel):
    """Metadata summary of an indexed academic document."""

    document_id: str
    document_name: str
    document_type: str
    category: str
    academic_year: str | None = None
    chunk_count: int
    source_file: str


class DocumentUploadResponse(BaseModel):
    """Result of document upload and security validation."""

    filename: str
    status: str
    file_size_bytes: int
    sha256_hash: str
    is_duplicate: bool
    message: str


class HealthResponse(BaseModel):
    """System health and operational status."""

    status: str
    app_name: str
    version: str
    llm_provider: str
    embedding_provider: str
    vectorstore_records: int
    bm25_indexed: bool
    llm_model: str | None = None
    llm_available: bool = True
    llm_status_message: str = "Available"

