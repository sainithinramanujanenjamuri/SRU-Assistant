"""Unit tests for document loaders (PDF, DOCX, TXT), error handling, and raw extraction preservation."""

from pathlib import Path

import pytest

from ingestion.loaders import (
    CorruptedDocumentError,
    DOCXLoader,
    EmptyDocumentError,
    PDFLoader,
    TXTLoader,
    UnsupportedDocumentError,
    get_loader_for_file,
)
from ingestion.models import ElementType
from tests.fixtures.fixture_generator import (
    create_synthetic_docx,
    create_synthetic_pdf,
    create_synthetic_txt,
)


def test_txt_loader_success(tmp_path: Path) -> None:
    """Verify TXTLoader parses lines and assigns 1-indexed line numbers."""
    content = "SR University Circular\nDate: 12-09-2026\nSemester VII classes commence on Monday."
    txt_file = create_synthetic_txt(tmp_path / "notice.txt", content)

    loader = TXTLoader()
    assert loader.can_load(txt_file) is True

    extracted = loader.load(txt_file)
    assert extracted.file_name == "notice.txt"
    assert extracted.file_type == ".txt"
    assert extracted.raw_text == content
    assert len(extracted.elements) == 3

    # Check line provenance
    assert extracted.elements[0].provenance.line_number == 1
    assert extracted.elements[1].provenance.line_number == 2
    assert extracted.elements[2].provenance.line_number == 3


def test_docx_loader_success_with_table(tmp_path: Path) -> None:
    """Verify DOCXLoader extracts paragraphs, headings, and structured tables."""
    docx_file = create_synthetic_docx(
        tmp_path / "syllabus.docx",
        title="B.Tech Computer Science Syllabus",
        paragraphs=[
            "Heading: Course Structure",
            "This document describes the scheme of instruction for Semester VII.",
        ],
        table_data=(
            ["Course Code", "Course Title", "Credits"],
            [
                ["23CSE302T", "Natural Language Processing", "3"],
                ["23CSE303T", "Compiler Design", "3"],
            ],
        ),
    )

    loader = DOCXLoader()
    assert loader.can_load(docx_file) is True

    extracted = loader.load(docx_file)
    assert extracted.file_name == "syllabus.docx"
    assert extracted.file_type == ".docx"
    assert len(extracted.elements) >= 3

    # Find table element
    table_elems = [e for e in extracted.elements if e.element_type == ElementType.TABLE]
    assert len(table_elems) == 1
    tbl = table_elems[0]
    assert tbl.table_data is not None
    assert tbl.table_data.headers == ["Course Code", "Course Title", "Credits"]
    assert len(tbl.table_data.rows) == 2
    assert "23CSE302T" in tbl.content
    assert "|" in tbl.content  # Markdown representation


def test_pdf_loader_success(tmp_path: Path) -> None:
    """Verify PDFLoader extracts text and page numbers across multiple pages."""
    pdf_file = create_synthetic_pdf(
        tmp_path / "calendar.pdf",
        pages=[
            ["SR University Academic Calendar 2026-27", "Semester VII B.Tech"],
            ["Mid-Semester Examination I", "12 September 2026 to 16 September 2026"],
        ],
    )

    loader = PDFLoader()
    assert loader.can_load(pdf_file) is True

    extracted = loader.load(pdf_file)
    assert extracted.file_name == "calendar.pdf"
    assert extracted.file_type == ".pdf"
    assert extracted.extraction_metadata["total_pages"] == 2

    # Check page numbers
    page_nums = {e.provenance.page_number for e in extracted.elements}
    assert 1 in page_nums
    assert 2 in page_nums


def test_loader_factory_resolution(tmp_path: Path) -> None:
    """Verify loader factory selects the correct loader by extension."""
    txt_path = tmp_path / "doc.txt"
    pdf_path = tmp_path / "doc.pdf"
    docx_path = tmp_path / "doc.docx"

    assert isinstance(get_loader_for_file(txt_path), TXTLoader)
    assert isinstance(get_loader_for_file(pdf_path), PDFLoader)
    assert isinstance(get_loader_for_file(docx_path), DOCXLoader)

    with pytest.raises(UnsupportedDocumentError):
        get_loader_for_file(tmp_path / "doc.unsupported_ext")


def test_empty_document_raises_error(tmp_path: Path) -> None:
    """Verify zero-byte files raise EmptyDocumentError."""
    empty_file = tmp_path / "empty.txt"
    empty_file.write_bytes(b"")

    loader = TXTLoader()
    with pytest.raises(EmptyDocumentError):
        loader.load(empty_file)


def test_corrupted_document_raises_error(tmp_path: Path) -> None:
    """Verify invalid / corrupted binary documents raise CorruptedDocumentError."""
    corrupted_pdf = tmp_path / "corrupted.pdf"
    corrupted_pdf.write_bytes(b"Not a valid PDF file stream at all!")

    loader = PDFLoader()
    with pytest.raises(CorruptedDocumentError):
        loader.load(corrupted_pdf)

    corrupted_docx = tmp_path / "corrupted.docx"
    corrupted_docx.write_bytes(b"Not a valid DOCX zip stream at all!")
    docx_loader = DOCXLoader()
    with pytest.raises(CorruptedDocumentError):
        docx_loader.load(corrupted_docx)


def test_raw_extraction_preservation(tmp_path: Path) -> None:
    """Verify that ExtractedDocument preserves original raw text and element stream unaltered."""
    raw_content = "Raw line 1\n\n   Raw line 2 with spaces   \nRaw line 3"
    txt_file = create_synthetic_txt(tmp_path / "raw.txt", raw_content)

    loader = TXTLoader()
    extracted = loader.load(txt_file)

    assert extracted.raw_text == raw_content
    # Elements exist and hold the raw contents
    assert len(extracted.elements) == 3
    assert extracted.elements[1].content == "Raw line 2 with spaces"
