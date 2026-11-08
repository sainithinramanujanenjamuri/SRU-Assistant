"""Unit tests for CitationMapper (claim-evidence alignment, provenance extraction, no-fake-data guarantee)."""

from citations.citation_mapper import CitationMapper
from citations.models import ClaimItem
from generation.models import RetrievedEvidence


def test_citation_mapper_provenance_parsing_valid_page() -> None:
    """Verify page number extraction from page_info and metadata."""
    mapper = CitationMapper()
    ev = RetrievedEvidence(
        chunk_id="chunk_1",
        document_id="doc_hash_1",
        document_name="Academic_Calendar_2026_27.pdf",
        page_info="p. 3",
        section_path="Academic Calendar > Examination Schedule",
        text="Exams begin 12 September 2026.",
        score=0.9,
        metadata={"page_number": 3, "section_title": "Examination Schedule"},
    )
    prov = mapper.extract_provenance(ev)
    assert prov["page"] == 3
    assert prov["page_info"] == "p. 3"
    assert "Examination Schedule" in prov["section"]
    assert "Academic Calendar 2026-27 — p. 3" in prov["source"]


def test_citation_mapper_provenance_missing_page_never_fabricated() -> None:
    """Verify that when page number is missing, mapper outputs None and 'p. N/A', never guessing a page number."""
    mapper = CitationMapper()
    ev = RetrievedEvidence(
        chunk_id="chunk_2",
        document_id="doc_hash_2",
        document_name="Regulations.pdf",
        page_info="p. N/A",
        section_path="N/A",
        text="Attendance requirement is 75%.",
        score=0.85,
        metadata={},  # No page_number
    )
    prov = mapper.extract_provenance(ev)
    assert prov["page"] is None
    assert prov["page_info"] == "p. N/A"
    assert prov["section"] == "N/A"
    assert "Regulations — p. N/A" in prov["source"]


def test_citation_mapper_provenance_malformed_page_handled_safely() -> None:
    """Verify malformed page strings fall back safely to None and 'p. N/A' rather than crashing or guessing."""
    mapper = CitationMapper()
    ev = RetrievedEvidence(
        chunk_id="chunk_3",
        document_id="doc_hash_3",
        document_name="Handbook.pdf",
        page_info="Unknown section",
        section_path="N/A",
        text="Some university info.",
        score=0.7,
        metadata={"page_number": "not_a_number"},
    )
    prov = mapper.extract_provenance(ev)
    assert prov["page"] is None
    assert prov["page_info"] in {"p. N/A", "Unknown section"}


def test_citation_mapper_claim_matching_and_reuse() -> None:
    """Verify claims matching the same evidence chunk share the same sequential citation ID."""
    mapper = CitationMapper(min_match_score=0.40)
    ev = RetrievedEvidence(
        chunk_id="chunk_cal_01",
        document_id="doc_cal_1",
        document_name="Academic_Calendar_2026_27.pdf",
        page_info="p. 3",
        section_path="Examination Schedule",
        text="Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026 for all B.Tech students.",
        score=0.95,
        metadata={"page_number": 3},
    )

    claims = [
        ClaimItem(
            claim_id="claim_1",
            claim_text="Mid-Semester Examination I begins on 12 September 2026.",
            claim_type="date",
            entities=["12 September 2026"],
        ),
        ClaimItem(
            claim_id="claim_2",
            claim_text="Examinations conclude on 16 September 2026 for all B.Tech students.",
            claim_type="date",
            entities=["16 September 2026"],
        ),
    ]

    mapped_claims, citations = mapper.map_claims_to_evidence(claims, [ev])

    # Both claims should be supported and share citation ID "1"
    assert len(citations) == 1
    assert citations[0].citation_id == "1"
    assert citations[0].document_name == "Academic_Calendar_2026_27.pdf"

    assert mapped_claims[0].is_supported is True
    assert mapped_claims[0].associated_citation_ids == ["1"]

    assert mapped_claims[1].is_supported is True
    assert mapped_claims[1].associated_citation_ids == ["1"]


def test_citation_mapper_multi_document_mapping() -> None:
    """Verify distinct evidence chunks from different documents get separate sequential citation IDs."""
    mapper = CitationMapper(min_match_score=0.40)
    ev1 = RetrievedEvidence(
        chunk_id="chunk_syl_1",
        document_id="doc_syl_1",
        document_name="Syllabus_23CSE302T.pdf",
        page_info="p. 1",
        section_path="Objectives",
        text="23CSE302T covers Advanced Data Structures including binary search trees.",
        score=0.9,
        metadata={"page_number": 1},
    )
    ev2 = RetrievedEvidence(
        chunk_id="chunk_cal_1",
        document_id="doc_cal_1",
        document_name="Academic_Calendar_2026_27.pdf",
        page_info="p. 3",
        section_path="Schedule",
        text="Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026.",
        score=0.88,
        metadata={"page_number": 3},
    )

    claims = [
        ClaimItem(
            claim_id="claim_1",
            claim_text="23CSE302T covers Advanced Data Structures including binary search trees.",
            claim_type="factual",
            entities=["23CSE302T"],
        ),
        ClaimItem(
            claim_id="claim_2",
            claim_text="Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026.",
            claim_type="date",
            entities=["12 September 2026", "16 September 2026"],
        ),
    ]

    mapped_claims, citations = mapper.map_claims_to_evidence(claims, [ev1, ev2])

    assert len(citations) == 2
    assert citations[0].citation_id == "1"
    assert citations[0].document_name == "Syllabus_23CSE302T.pdf"
    assert citations[1].citation_id == "2"
    assert citations[1].document_name == "Academic_Calendar_2026_27.pdf"

    assert mapped_claims[0].associated_citation_ids == ["1"]
    assert mapped_claims[1].associated_citation_ids == ["2"]


def test_citation_mapper_unsupported_claim_not_falsely_cited() -> None:
    """Verify that an unsupported claim with no matching evidence is NOT assigned a nearest citation."""
    mapper = CitationMapper(min_match_score=0.40)
    ev = RetrievedEvidence(
        chunk_id="chunk_cal_1",
        document_id="doc_cal_1",
        document_name="Academic_Calendar_2026_27.pdf",
        page_info="p. 3",
        section_path="Schedule",
        text="Mid-Semester Examination I is on 12 September 2026.",
        score=0.9,
    )
    # Claim about unrelated course and fee payment
    unsupported_claim = ClaimItem(
        claim_id="claim_unsupported",
        claim_text="Tuition fee of 50000 rupees must be paid before November 30.",
        claim_type="policy",
        entities=[],
    )

    mapped_claims, citations = mapper.map_claims_to_evidence([unsupported_claim], [ev])

    assert len(citations) == 0
    assert mapped_claims[0].is_supported is False
    assert mapped_claims[0].associated_citation_ids == []
