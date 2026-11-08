"""Unit tests for metadata extraction and strict non-fabrication enforcement."""

from pathlib import Path

from ingestion.loaders import TXTLoader
from ingestion.metadata import MetadataExtractor
from ingestion.processors import StructureDetector
from tests.fixtures.fixture_generator import create_synthetic_txt


def test_metadata_extraction_with_explicit_evidence(tmp_path: Path) -> None:
    """Verify metadata is extracted accurately when explicit evidence is present."""
    content = (
        "SR University B.Tech Syllabus\n"
        "Department of Computer Science and Engineering\n"
        "Academic Regulations R23\n"
        "Semester VII, Academic Year 2026-27"
    )
    doc_path = create_synthetic_txt(tmp_path / "syllabus_evidence.txt", content)

    loader = TXTLoader()
    extracted = loader.load(doc_path)

    detector = StructureDetector()
    structures = detector.detect_structures(extracted.elements, extracted.raw_text)

    extractor = MetadataExtractor()
    meta = extractor.extract_metadata(extracted, structures)

    assert meta.document_id == extracted.document_id
    assert meta.department == "Computer Science and Engineering"
    assert meta.academic_year == "2026-27"
    assert meta.semester == "Semester VII"
    assert "R23" in meta.regulations
    assert meta.program == "B.Tech"
    assert meta.category == "syllabus"
    assert meta.file_size_bytes > 0


def test_metadata_non_fabrication_rule(tmp_path: Path) -> None:
    """Verify that absent metadata fields remain None rather than being fabricated or guessed."""
    # Document with general content only - no department, semester, regulation, or year
    content = "General Campus Library Regulations\nOpen Monday to Friday 9 AM to 5 PM.\nSilence must be maintained."
    doc_path = create_synthetic_txt(tmp_path / "library_notice.txt", content)

    loader = TXTLoader()
    extracted = loader.load(doc_path)

    detector = StructureDetector()
    structures = detector.detect_structures(extracted.elements, extracted.raw_text)

    extractor = MetadataExtractor()
    meta = extractor.extract_metadata(extracted, structures)

    # All fields must remain None / empty
    assert meta.department is None, "Department must not be fabricated"
    assert meta.semester is None, "Semester must not be fabricated"
    assert meta.academic_year is None, "Academic year must not be fabricated"
    assert meta.program is None, "Program must not be fabricated"
    assert meta.regulations == [], "Regulations must not be fabricated"
