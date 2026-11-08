"""Integration tests for DocumentPipeline, end-to-end processing, and batch error isolation."""

import json
from pathlib import Path

from ingestion.models import ProcessedDocument
from ingestion.pipeline import DocumentPipeline
from tests.fixtures.fixture_generator import (
    create_synthetic_docx,
    create_synthetic_pdf,
    create_synthetic_txt,
)


def test_end_to_end_single_file_processing(tmp_path: Path) -> None:
    """Verify single document end-to-end processing, JSON serialization, and structure preservation."""
    docx_file = create_synthetic_docx(
        tmp_path / "nlp_syllabus.docx",
        title="B.Tech Syllabus for NLP",
        paragraphs=[
            "Department of Computer Science and Engineering",
            "Academic Regulations R23 - Semester VII",
            "Course Code: 23CSE302T",
        ],
        table_data=(
            ["Unit", "Topic", "Hours"],
            [
                ["Unit I", "Text Processing and N-grams", "8"],
                ["Unit II", "Syntactic Parsing", "10"],
            ],
        ),
    )

    pipeline = DocumentPipeline()
    processed_doc = pipeline.process_file(docx_file)

    assert isinstance(processed_doc, ProcessedDocument)
    assert processed_doc.document_id is not None
    assert processed_doc.metadata.department == "Computer Science and Engineering"
    assert "R23" in processed_doc.metadata.regulations
    assert processed_doc.metadata.semester == "Semester VII"
    assert "23CSE302T" in processed_doc.academic_structures.course_codes
    assert processed_doc.raw_elements_count > 0
    assert len(processed_doc.elements) > 0

    # Test serialization to JSON and reload
    json_path = tmp_path / "output" / f"{processed_doc.document_id}.json"
    processed_doc.save_to_file(json_path)

    assert json_path.exists()
    loaded_data = json.loads(json_path.read_text(encoding="utf-8"))
    assert loaded_data["document_id"] == processed_doc.document_id
    assert loaded_data["metadata"]["document_name"] == "nlp_syllabus.docx"


def test_batch_directory_processing_with_failure_isolation(tmp_path: Path) -> None:
    """Verify directory batch processing isolates errors from bad files and processes valid ones."""
    input_dir = tmp_path / "raw_docs"
    output_dir = tmp_path / "processed_docs"
    input_dir.mkdir()

    # 1. Valid TXT
    create_synthetic_txt(
        input_dir / "valid_notice.txt",
        "SR University Notice\nMid-Semester Examination I starting 12 September 2026.",
    )

    # 2. Valid DOCX with table
    create_synthetic_docx(
        input_dir / "valid_curriculum.docx",
        title="Department of ECE Regulations R20",
        paragraphs=["Scheme of Instruction"],
        table_data=(["Code", "Subject"], [["20EC201", "Signals and Systems"]]),
    )

    # 3. Valid PDF
    create_synthetic_pdf(
        input_dir / "valid_calendar.pdf",
        pages=[["SR University Academic Calendar 2026-27", "All Departments"]],
    )

    # 4. Corrupted PDF (invalid stream)
    corrupt_pdf = input_dir / "corrupted_file.pdf"
    corrupt_pdf.write_bytes(b"Garbage non-PDF data")

    # 5. Empty TXT (zero bytes)
    empty_txt = input_dir / "empty_doc.txt"
    empty_txt.write_bytes(b"")

    pipeline = DocumentPipeline()
    batch_result = pipeline.process_directory(input_dir, output_dir)

    assert batch_result.total_files_found == 5
    assert batch_result.successful_count == 3
    assert batch_result.failed_count == 2
    assert len(batch_result.failures) == 2

    # Verify failure details were captured without crashing
    failed_file_names = {Path(f.file_path).name for f in batch_result.failures}
    assert "corrupted_file.pdf" in failed_file_names
    assert "empty_doc.txt" in failed_file_names

    # Verify 3 valid JSON output files exist
    output_jsons = list(output_dir.glob("*.json"))
    assert len(output_jsons) == 3
