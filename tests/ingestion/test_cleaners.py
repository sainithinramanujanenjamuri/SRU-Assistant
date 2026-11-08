"""Unit tests for DocumentCleaner and conservative header/footer filtering."""

from pathlib import Path

from ingestion.loaders import PDFLoader
from ingestion.processors import DocumentCleaner
from tests.fixtures.fixture_generator import (
    create_synthetic_pdf,
)


def test_text_normalization_whitespace_and_unicode() -> None:
    """Verify that unicode characters and excessive whitespace are properly normalized."""
    dirty_text = "  SR\u00a0University   \t Academic\x00\x08Calendar   \n\n\n   2026-27   "
    clean_text = DocumentCleaner.normalize_text(dirty_text)

    assert "SR University" in clean_text
    assert "\x00" not in clean_text
    assert "\x08" not in clean_text
    assert "Academic Calendar" in clean_text
    assert "2026-27" in clean_text


def test_conservative_header_removal_drops_boilerplate(tmp_path: Path) -> None:
    """Verify that purely repetitive non-academic boilerplate headers are removed across >=3 pages."""
    pdf_file = create_synthetic_pdf(
        tmp_path / "multi_page.pdf",
        pages=[
            ["Document Header Info", "Content on page one", "Page Footer Note"],
            ["Document Header Info", "Content on page two", "Page Footer Note"],
            ["Document Header Info", "Content on page three", "Page Footer Note"],
            ["Document Header Info", "Content on page four", "Page Footer Note"],
        ],
    )

    loader = PDFLoader()
    extracted = loader.load(pdf_file)

    cleaner = DocumentCleaner(header_footer_threshold=0.75)
    cleaned = cleaner.clean(extracted)

    contents = [e.content for e in cleaned]
    assert "Document Header Info" not in contents
    assert "Page Footer Note" not in contents
    assert "Content on page one" in contents
    assert "Content on page four" in contents


def test_conservative_header_removal_protects_academic_content(tmp_path: Path) -> None:
    """Verify that repeated lines containing academic entities (course codes, R23, exams) are PROTECTED."""
    pdf_file = create_synthetic_pdf(
        tmp_path / "academic_headers.pdf",
        pages=[
            ["SR University B.Tech Regulation R23", "Unit 1 Content", "Exam Schedule 2026-27"],
            ["SR University B.Tech Regulation R23", "Unit 2 Content", "Exam Schedule 2026-27"],
            ["SR University B.Tech Regulation R23", "Unit 3 Content", "Exam Schedule 2026-27"],
            ["SR University B.Tech Regulation R23", "Unit 4 Content", "Exam Schedule 2026-27"],
        ],
    )

    loader = PDFLoader()
    extracted = loader.load(pdf_file)

    cleaner = DocumentCleaner(header_footer_threshold=0.75)
    cleaned = cleaner.clean(extracted)

    contents = [e.content for e in cleaned]
    # Essential academic lines must NOT be deleted
    assert any("Regulation R23" in c for c in contents)
    assert any("Exam Schedule 2026-27" in c for c in contents)


def test_short_documents_not_stripped_of_headers(tmp_path: Path) -> None:
    """Verify that documents with fewer than 3 pages are never stripped of potential headers."""
    pdf_file = create_synthetic_pdf(
        tmp_path / "two_page.pdf",
        pages=[
            ["Notice Header", "Page 1 Content"],
            ["Notice Header", "Page 2 Content"],
        ],
    )

    loader = PDFLoader()
    extracted = loader.load(pdf_file)

    cleaner = DocumentCleaner()
    cleaned = cleaner.clean(extracted)

    contents = [e.content for e in cleaned]
    assert "Notice Header" in contents
