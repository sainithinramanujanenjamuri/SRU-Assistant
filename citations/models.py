"""Data models for citations, claims, provenance tracking, and citation verification audits."""
from __future__ import annotations



from typing import Any, Literal


from pydantic import BaseModel, ConfigDict, Field, field_validator


class CitationItem(BaseModel):
    """First-class citation item representing the exact provenance of a grounded claim.

    Pipeline hierarchy:
    Document -> Page -> Section -> Chunk -> Retrieved Evidence -> Generated Claim -> Citation
    """

    model_config = ConfigDict(frozen=True)

    citation_id: str = Field(..., description="Deterministic sequential citation identifier (e.g. '1', '2')")
    document_id: str = Field(..., description="Canonical SHA-256 identifier of the source document")
    document_name: str = Field(..., description="Human-readable filename of the source document")
    page: int | None = Field(default=None, ge=1, description="Physical 1-indexed page number if present; None if unavailable")
    page_info: str = Field(default="p. N/A", description="Human-readable page string (e.g. 'p. 3' or 'p. N/A')")
    section: str = Field(default="N/A", description="Hierarchical section breadcrumb or title from document structure")
    chunk_id: str = Field(..., description="Unique chunk identifier from which evidence was retrieved")
    source: str = Field(..., description="Formatted provenance label (e.g. 'Academic Calendar 2026-27 — p. 3')")
    claim_text: str | None = Field(default=None, description="Exact factual claim supported by this citation")
    support_score: float | None = Field(
        default=None, ge=0.0, le=1.0, description="Verification support score in [0.0, 1.0] if audited"
    )
    is_verified: bool = Field(default=False, description="True if evidence chunk factually backs the attached claim")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional provenance or chunk metadata")

    @field_validator("page_info")
    @classmethod
    def validate_page_info(cls, v: str) -> str:
        if not v or not v.strip():
            return "p. N/A"
        return v.strip()


ClaimType = Literal["factual", "date", "policy", "general"]


class ClaimItem(BaseModel):
    """Discrete factual proposition extracted from a synthesized answer."""

    model_config = ConfigDict(frozen=True)

    claim_id: str = Field(..., description="Deterministic unique identifier for the extracted claim (e.g. 'claim_1')")
    claim_text: str = Field(..., description="Cleaned sentence or atomic assertion representing the claim")
    claim_type: ClaimType = Field(default="factual", description="Classification of claim content")
    associated_citation_ids: list[str] = Field(
        default_factory=list, description="Ordered list of citation IDs supporting this claim"
    )
    is_supported: bool = Field(
        default=False, description="True if claim is substantiated by at least one verified citation"
    )
    support_evidence_chunk_ids: list[str] = Field(
        default_factory=list, description="Chunk IDs identified as backing this claim"
    )
    support_score: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Calculated support confidence in [0.0, 1.0]"
    )
    entities: list[str] = Field(
        default_factory=list, description="Academic entities (courses, dates, regulations) referenced in claim"
    )


class CitationVerificationResult(BaseModel):
    """Comprehensive citation audit report evaluating claim-evidence factual support.

    Metrics defined:
    - citation_precision: verified supporting citations / total citations emitted
    - citation_recall: supported factual claims with >= 1 verified citation / total extractable factual claims
    - overall_support_score: weighted average of verified claim support scores in [0.0, 1.0]
    """

    model_config = ConfigDict(frozen=True)

    is_fully_supported: bool = Field(
        ..., description="True if all claims with citations are verified and no ungrounded claims exist"
    )
    overall_support_score: float = Field(
        ..., ge=0.0, le=1.0, description="Deterministic factual support score across claims in [0.0, 1.0]"
    )
    citation_precision: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of verified supporting citations to total citations emitted"
    )
    citation_recall: float = Field(
        ..., ge=0.0, le=1.0, description="Ratio of supported factual claims to total extractable factual claims"
    )
    claims: list[ClaimItem] = Field(default_factory=list, description="Detailed list of audited claims")
    citations: list[CitationItem] = Field(default_factory=list, description="Detailed list of citations emitted")
    unsupported_claims: list[str] = Field(
        default_factory=list, description="Text of claims that could not be supported by evidence"
    )
    unverified_citations: list[str] = Field(
        default_factory=list, description="Citation IDs that failed factual verification"
    )
    verification_latency_ms: float = Field(
        default=0.0, ge=0.0, description="Latency of citation verification processing in milliseconds"
    )
