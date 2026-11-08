"""Unit tests for CitationFormatter (inline_bracket, source_block, footnote styles)."""

from citations.formatter import CitationFormatter
from citations.models import CitationItem, ClaimItem


def test_formatter_inline_bracket_style() -> None:
    """Verify inline_bracket style attaches [1] markers to claim sentences and lists sources."""
    formatter = CitationFormatter()
    answer = "The mid-semester examinations are scheduled for 12 September 2026."
    cit = CitationItem(
        citation_id="1",
        document_id="doc_1",
        document_name="Academic_Calendar_2026_27.pdf",
        page=3,
        page_info="p. 3",
        section="Examination Schedule",
        chunk_id="chunk_1",
        source="Academic Calendar 2026-27 — p. 3",
    )
    claim = ClaimItem(
        claim_id="claim_1",
        claim_text="The mid-semester examinations are scheduled for 12 September 2026.",
        associated_citation_ids=["1"],
    )

    formatted = formatter.format(answer, [cit], [claim], style="inline_bracket")

    assert "[1]" in formatted
    assert "Sources:" in formatted
    assert "[1] Academic Calendar 2026-27 — p. 3" in formatted
    assert "Section: Examination Schedule" in formatted


def test_formatter_source_block_style() -> None:
    """Verify source_block style leaves answer text clean and appends a structured source block."""
    formatter = CitationFormatter()
    answer = "The mid-semester examinations are scheduled for 12 September 2026."
    cit = CitationItem(
        citation_id="1",
        document_id="doc_1",
        document_name="Academic_Calendar_2026_27.pdf",
        page=3,
        page_info="p. 3",
        section="Examination Schedule",
        chunk_id="chunk_1",
        source="Academic Calendar 2026-27 — p. 3",
    )

    formatted = formatter.format(answer, [cit], style="source_block")

    # Body should not have inline bracket markers
    assert "[1]" not in formatted
    assert "Source:" in formatted or "Sources:" in formatted
    assert "- Academic Calendar 2026-27 — p. 3" in formatted


def test_formatter_footnote_style() -> None:
    """Verify footnote style attaches superscript numerals and lists Footnotes at bottom."""
    formatter = CitationFormatter()
    answer = "The examination begins on 12 September 2026."
    cit = CitationItem(
        citation_id="1",
        document_id="doc_1",
        document_name="Academic_Calendar_2026_27.pdf",
        page=3,
        page_info="p. 3",
        section="Examination Schedule",
        chunk_id="chunk_1",
        source="Academic Calendar 2026-27 — p. 3",
    )
    claim = ClaimItem(
        claim_id="claim_1",
        claim_text="The examination begins on 12 September 2026.",
        associated_citation_ids=["1"],
    )

    formatted = formatter.format(answer, [cit], [claim], style="footnote")

    assert "¹" in formatted
    assert "Footnotes:" in formatted
    assert "¹ Academic Calendar 2026-27 — p. 3" in formatted


def test_formatter_multiple_citations_per_claim() -> None:
    """Verify multiple citations on a single claim format as '[1, 2]'."""
    formatter = CitationFormatter()
    answer = "Course 23CSE302T exam is on 12 September 2026."
    cit1 = CitationItem(citation_id="1", document_id="d1", document_name="Syllabus.pdf", chunk_id="c1", source="Syllabus — p. 1")
    cit2 = CitationItem(citation_id="2", document_id="d2", document_name="Calendar.pdf", chunk_id="c2", source="Calendar — p. 3")
    claim = ClaimItem(
        claim_id="claim_1",
        claim_text="Course 23CSE302T exam is on 12 September 2026.",
        associated_citation_ids=["1", "2"],
    )

    formatted = formatter.format(answer, [cit1, cit2], [claim], style="inline_bracket")

    assert "[1, 2]" in formatted
    assert "[1] Syllabus — p. 1" in formatted
    assert "[2] Calendar — p. 3" in formatted


def test_formatter_missing_page_and_section() -> None:
    """Verify formatting handles missing page ('p. N/A') and missing section gracefully."""
    formatter = CitationFormatter()
    answer = "Continuous assessment requires 3 assignments."
    cit = CitationItem(
        citation_id="1",
        document_id="doc_1",
        document_name="Circular.pdf",
        page=None,
        page_info="p. N/A",
        section="N/A",
        chunk_id="c_1",
        source="Circular — p. N/A",
    )
    claim = ClaimItem(
        claim_id="claim_1",
        claim_text="Continuous assessment requires 3 assignments.",
        associated_citation_ids=["1"],
    )

    formatted = formatter.format(answer, [cit], [claim], style="inline_bracket")

    assert "Circular — p. N/A" in formatted
    # Section line should be omitted if "N/A"
    assert "Section: N/A" not in formatted


def test_formatter_empty_citations_returns_clean_answer() -> None:
    """Verify empty citations list returns the answer text completely unmodified."""
    formatter = CitationFormatter()
    fallback = "I couldn't find sufficient information in the available SR University documents to answer this accurately."
    formatted = formatter.format(fallback, [], [])
    assert formatted == fallback
