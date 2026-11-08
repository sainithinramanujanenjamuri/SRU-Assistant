"""Unit tests and adversarial test cases for CitationVerifier (Section 22 & 23)."""

from citations.citation_verifier import CitationVerifier
from citations.models import CitationItem, ClaimItem
from generation.models import RetrievedEvidence


def test_adversarial_case_a_course_present_but_exam_missing() -> None:
    """Case A: Claim asserts exam date for 23CSE302T, but evidence only mentions course description.

    Expected: Unsupported (Claim != Entity containment).
    """
    verifier = CitationVerifier(min_support_score=0.50, require_exact_entities=True)
    ev = RetrievedEvidence(
        chunk_id="chunk_a",
        document_id="doc_a",
        document_name="Syllabus_23CSE302T.pdf",
        text="23CSE302T is a Machine Learning course covering neural networks and optimization.",
        score=0.9,
    )
    cit = CitationItem(
        citation_id="1",
        document_id="doc_a",
        document_name="Syllabus_23CSE302T.pdf",
        chunk_id="chunk_a",
        source="Syllabus 23CSE302T — p. 1",
    )
    claim = ClaimItem(
        claim_id="claim_a",
        claim_text="23CSE302T has an exam on 15 September 2026.",
        claim_type="date",
        associated_citation_ids=["1"],
        entities=["23CSE302T", "15 September 2026"],
    )

    result = verifier.verify_citations([claim], [cit], [ev])
    assert result.is_fully_supported is False
    assert result.citation_recall == 0.0
    assert "claim_a" in [c.claim_id for c in result.claims if not c.is_supported]
    assert len(result.unsupported_claims) == 1


def test_adversarial_case_b_exact_match_supported() -> None:
    """Case B: Claim asserts exam date for 23CSE302T, and evidence contains course code and exam date.

    Expected: Supported.
    """
    verifier = CitationVerifier(min_support_score=0.50, require_exact_entities=True)
    ev = RetrievedEvidence(
        chunk_id="chunk_b",
        document_id="doc_b",
        document_name="Exam_Circular.pdf",
        text="23CSE302T mid examination is scheduled for 15 September 2026 in Hall A.",
        score=0.95,
    )
    cit = CitationItem(
        citation_id="1",
        document_id="doc_b",
        document_name="Exam_Circular.pdf",
        chunk_id="chunk_b",
        source="Exam Circular — p. 1",
    )
    claim = ClaimItem(
        claim_id="claim_b",
        claim_text="23CSE302T has an exam on 15 September 2026.",
        claim_type="date",
        associated_citation_ids=["1"],
        entities=["23CSE302T", "15 September 2026"],
    )

    result = verifier.verify_citations([claim], [cit], [ev])
    assert result.is_fully_supported is True
    assert result.citation_precision == 1.0
    assert result.citation_recall == 1.0
    assert result.claims[0].is_supported is True
    assert result.citations[0].is_verified is True


def test_adversarial_case_c_different_course_code_unsupported() -> None:
    """Case C: Evidence has exam on 15 September for 23CSE401T, but claim asserts 23CSE302T.

    Expected: Unsupported (Course code precision check fails).
    """
    verifier = CitationVerifier(min_support_score=0.50, require_exact_entities=True)
    ev = RetrievedEvidence(
        chunk_id="chunk_c",
        document_id="doc_c",
        document_name="Exam_Circular.pdf",
        text="23CSE401T mid examination is scheduled for 15 September 2026.",
        score=0.9,
    )
    cit = CitationItem(
        citation_id="1",
        document_id="doc_c",
        document_name="Exam_Circular.pdf",
        chunk_id="chunk_c",
        source="Exam Circular — p. 1",
    )
    claim = ClaimItem(
        claim_id="claim_c",
        claim_text="23CSE302T has an exam on 15 September 2026.",
        claim_type="date",
        associated_citation_ids=["1"],
        entities=["23CSE302T", "15 September 2026"],
    )

    result = verifier.verify_citations([claim], [cit], [ev])
    assert result.is_fully_supported is False
    assert result.citation_recall == 0.0
    assert result.citations[0].is_verified is False


def test_adversarial_case_d_multi_chunk_relationship() -> None:
    """Case D: Claim requires combining course code and exam date across two chunks.

    Expected: When both chunks are cited together, relationship is supported across the combined evidence.
    """
    verifier = CitationVerifier(min_support_score=0.50, require_exact_entities=True)
    ev1 = RetrievedEvidence(
        chunk_id="chunk_d1",
        document_id="doc_d1",
        document_name="Syllabus.pdf",
        text="Course 23CSE302T is Machine Learning.",
        score=0.85,
    )
    ev2 = RetrievedEvidence(
        chunk_id="chunk_d2",
        document_id="doc_d2",
        document_name="Calendar.pdf",
        text="Mid-Semester examination for Machine Learning is on 15 September 2026.",
        score=0.88,
    )
    cit1 = CitationItem(citation_id="1", document_id="doc_d1", document_name="Syllabus.pdf", chunk_id="chunk_d1", source="Syllabus — p. 1")
    cit2 = CitationItem(citation_id="2", document_id="doc_d2", document_name="Calendar.pdf", chunk_id="chunk_d2", source="Calendar — p. 2")

    claim = ClaimItem(
        claim_id="claim_d",
        claim_text="23CSE302T has an exam on 15 September 2026.",
        claim_type="date",
        associated_citation_ids=["1", "2"],
        entities=["23CSE302T", "15 September 2026"],
    )

    result = verifier.verify_citations([claim], [cit1, cit2], [ev1, ev2])
    assert result.is_fully_supported is True
    assert result.citation_recall == 1.0


def test_citation_precision_and_recall_calculation() -> None:
    """Verify exact precision and recall formulas:

    citation_precision = verified citations / total citations emitted
    citation_recall = supported claims / total claims
    """
    verifier = CitationVerifier(min_support_score=0.50)
    ev1 = RetrievedEvidence(
        chunk_id="chunk_1",
        document_id="doc_1",
        document_name="Doc1.pdf",
        text="Mid examination is on 12 September 2026.",
        score=0.9,
    )
    ev2 = RetrievedEvidence(
        chunk_id="chunk_2",
        document_id="doc_2",
        document_name="Doc2.pdf",
        text="General campus safety guidelines.",
        score=0.8,
    )
    cit1 = CitationItem(citation_id="1", document_id="doc_1", document_name="Doc1.pdf", chunk_id="chunk_1", source="Doc1 — p. 1")
    cit2 = CitationItem(citation_id="2", document_id="doc_2", document_name="Doc2.pdf", chunk_id="chunk_2", source="Doc2 — p. 1")

    claim1 = ClaimItem(
        claim_id="claim_1",
        claim_text="Mid examination is on 12 September 2026.",
        claim_type="date",
        associated_citation_ids=["1"],
        entities=["12 September 2026"],
    )
    # Claim 2 is attached to irrelevant chunk 2
    claim2 = ClaimItem(
        claim_id="claim_2",
        claim_text="Attendance requirement is 85%.",
        claim_type="policy",
        associated_citation_ids=["2"],
        entities=[],
    )

    result = verifier.verify_citations([claim1, claim2], [cit1, cit2], [ev1, ev2])

    # 1 of 2 citations verified -> precision = 0.50
    assert result.citation_precision == 0.50
    # 1 of 2 claims supported -> recall = 0.50
    assert result.citation_recall == 0.50
    assert result.is_fully_supported is False
    assert result.unsupported_claims == ["Attendance requirement is 85%."]
    assert result.unverified_citations == ["2"]
