"""Tests verifying that unbroken provenance survives across all processing stages."""

from pathlib import Path

from ingestion.loaders import DOCXLoader, PDFLoader, TXTLoader
from ingestion.models import ElementType
from ingestion.processors import DocumentCleaner
from tests.fixtures.fixture_generator import (
    create_synthetic_docx,
    create_synthetic_pdf,
    create_synthetic_txt,
)


def test_pdf_page_provenance_survives_cleaning(tmp_path: Path) -> None:
    """Verify that page numbers in provenance survive cleaning without modification."""
    pdf_file = create_synthetic_pdf(
        tmp_path / "doc.pdf",
        pages=[
            ["Page 1 Header", "Page 1 Content"],
            ["Page 2 Header", "Page 2 Content"],
            ["Page 3 Header", "Page 3 Content"],
        ],
    )

    loader = PDFLoader()
    extracted = loader.load(pdf_file)
    cleaner = DocumentCleaner()
    cleaned_elements = cleaner.clean(extracted)

    # Check that provenance on each cleaned element matches extracted
    for elem in cleaned_elements:
        assert elem.provenance.document_id == extracted.document_id
        assert elem.provenance.source_file == "doc.pdf"
        assert elem.provenance.page_number in (1, 2, 3)
        assert elem.provenance.structural_index > 0


def test_txt_line_provenance_survives_cleaning(tmp_path: Path) -> None:
    """Verify that 1-indexed line numbers survive text cleaning."""
    txt_file = create_synthetic_txt(
        tmp_path / "doc.txt",
        "Line 1: Regulations\n\nLine 3: Details\n\nLine 5: Examination",
    )

    loader = TXTLoader()
    extracted = loader.load(txt_file)
    cleaner = DocumentCleaner()
    cleaned_elements = cleaner.clean(extracted)

    assert len(cleaned_elements) == 3
    assert cleaned_elements[0].provenance.line_number == 1
    assert cleaned_elements[1].provenance.line_number == 3
    assert cleaned_elements[2].provenance.line_number == 5


def test_table_provenance_and_grid_preservation(tmp_path: Path) -> None:
    """Verify that DOCX tables retain full structural grid, cell data, and provenance."""
    docx_file = create_synthetic_docx(
        tmp_path / "table_doc.docx",
        title="Curriculum Table",
        paragraphs=["Scheme of Instruction"],
        table_data=(
            ["Course Code", "Course Name", "Credits"],
            [
                ["23CSE302T", "Natural Language Processing", "3"],
                ["23CSE303T", "Compiler Design", "3"],
            ],
        ),
    )

    loader = DOCXLoader()
    extracted = loader.load(docx_file)
    cleaner = DocumentCleaner()
    cleaned_elements = cleaner.clean(extracted)

    table_elements = [e for e in cleaned_elements if e.element_type == ElementType.TABLE]
    assert len(table_elements) == 1
    tbl = table_elements[0]

    # Grid preservation
    assert tbl.table_data is not None
    assert tbl.table_data.headers == ["Course Code", "Course Name", "Credits"]
    assert len(tbl.table_data.rows) == 2
    assert tbl.table_data.num_rows == 3  # header + 2 rows
    assert tbl.table_data.num_cols == 3

    # Provenance preservation
    assert tbl.provenance.document_id == extracted.document_id
    assert tbl.provenance.source_file == "table_doc.docx"
    assert tbl.provenance.structural_index > 0
