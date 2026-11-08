"""SRU Assistant - Citations and provenance tracking package."""

from typing import TYPE_CHECKING

from citations.models import (
    CitationItem,
    CitationVerificationResult,
    ClaimItem,
    ClaimType,
)

if TYPE_CHECKING:
    from citations.citation_mapper import CitationMapper
    from citations.citation_verifier import CitationVerifier
    from citations.claim_extractor import ClaimExtractor
    from citations.formatter import CitationFormatter


def __getattr__(name: str):
    if name == "ClaimExtractor":
        from citations.claim_extractor import ClaimExtractor

        return ClaimExtractor
    if name == "CitationMapper":
        from citations.citation_mapper import CitationMapper

        return CitationMapper
    if name == "CitationVerifier":
        from citations.citation_verifier import CitationVerifier

        return CitationVerifier
    if name == "CitationFormatter":
        from citations.formatter import CitationFormatter

        return CitationFormatter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "CitationFormatter",
    "CitationItem",
    "CitationMapper",
    "CitationVerificationResult",
    "CitationVerifier",
    "ClaimExtractor",
    "ClaimItem",
    "ClaimType",
]
