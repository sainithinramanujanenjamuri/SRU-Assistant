"""Unit tests for citation and claim data models (validation, serialization, frozen behavior)."""

import pytest
from pydantic import ValidationError

from citations.models import (
    CitationItem,
    CitationVerificationResult,
    ClaimItem,
)


def test_citation_item_valid_creation() -> None:
    """Verify that a CitationItem can be created with valid provenance fields."""
    cit = CitationItem(
        citation_id="1",
        document_id="doc_hash_123",
        document_name="Academic_Calendar_2026_27.pdf",
        page=3,
        page_info="p. 3",
        section="Examination Schedule",
        chunk_id="chunk_001",
        source="Academic Calendar 2026-27 — p. 3",
        claim_text="Exams begin on September 12.",
        support_score=0.95,
        is_verified=True,
    )
    assert cit.citation_id == "1"
    assert cit.page == 3
    assert cit.page_info == "p. 3"
    assert cit.is_verified is True
    assert cit.support_score == 0.95


def test_citation_item_missing_page_defaults() -> None:
    """Verify CitationItem handles missing page gracefully without inventing page numbers."""
    cit = CitationItem(
        citation_id="2",
        document_id="doc_hash_456",
        document_name="Regulations.pdf",
        page=None,
        page_info="p. N/A",
        section="N/A",
        chunk_id="chunk_002",
        source="Regulations — p. N/A",
    )
    assert cit.page is None
    assert cit.page_info == "p. N/A"
    assert cit.section == "N/A"


def test_citation_item_immutable_frozen() -> None:
    """Verify CitationItem is frozen and prevents field mutation."""
    cit = CitationItem(
        citation_id="1",
        document_id="doc_1",
        document_name="doc.pdf",
        chunk_id="c_1",
        source="doc — p. N/A",
    )
    with pytest.raises(ValidationError):
        cit.is_verified = True  # type: ignore[misc]


def test_citation_item_invalid_score_bounds() -> None:
    """Verify CitationItem rejects support_score outside [0.0, 1.0]."""
    with pytest.raises(ValidationError):
        CitationItem(
            citation_id="1",
            document_id="doc_1",
            document_name="doc.pdf",
            chunk_id="c_1",
            source="doc",
            support_score=1.5,
        )

    with pytest.raises(ValidationError):
        CitationItem(
            citation_id="1",
            document_id="doc_1",
            document_name="doc.pdf",
            chunk_id="c_1",
            source="doc",
            support_score=-0.1,
        )


def test_claim_item_creation_and_frozen() -> None:
    """Verify ClaimItem validation and immutability."""
    claim = ClaimItem(
        claim_id="claim_1",
        claim_text="Mid exams are from 12 to 16 September 2026.",
        claim_type="date",
        associated_citation_ids=["1"],
        is_supported=True,
        support_evidence_chunk_ids=["chunk_1"],
        support_score=0.92,
        entities=["12 September 2026", "16 September 2026"],
    )
    assert claim.claim_id == "claim_1"
    assert claim.claim_type == "date"
    assert claim.is_supported is True

    with pytest.raises(ValidationError):
        claim.support_score = 1.2  # type: ignore[misc]


def test_claim_item_invalid_type() -> None:
    """Verify ClaimItem rejects unapproved claim_type values."""
    with pytest.raises(ValidationError):
        ClaimItem(
            claim_id="claim_1",
            claim_text="Some text",
            claim_type="unknown_type",  # type: ignore[arg-type]
        )


def test_citation_verification_result_serialization() -> None:
    """Verify CitationVerificationResult validates metrics and serializes to dict/JSON."""
    cit = CitationItem(
        citation_id="1",
        document_id="doc_1",
        document_name="Calendar.pdf",
        page=3,
        page_info="p. 3",
        section="Schedule",
        chunk_id="chunk_1",
        source="Calendar — p. 3",
        support_score=0.9,
        is_verified=True,
    )
    claim = ClaimItem(
        claim_id="claim_1",
        claim_text="Exams on September 12.",
        claim_type="date",
        associated_citation_ids=["1"],
        is_supported=True,
        support_evidence_chunk_ids=["chunk_1"],
        support_score=0.9,
        entities=["September 12"],
    )
    result = CitationVerificationResult(
        is_fully_supported=True,
        overall_support_score=0.9,
        citation_precision=1.0,
        citation_recall=1.0,
        claims=[claim],
        citations=[cit],
        unsupported_claims=[],
        unverified_citations=[],
        verification_latency_ms=1.5,
    )
    dumped = result.model_dump()
    assert dumped["is_fully_supported"] is True
    assert dumped["citation_precision"] == 1.0
    assert len(dumped["claims"]) == 1
    assert dumped["claims"][0]["claim_id"] == "claim_1"
