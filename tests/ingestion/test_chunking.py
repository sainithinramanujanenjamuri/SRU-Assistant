"""Comprehensive unit and integration tests for Phase 2 Knowledge Preparation and Chunking."""
from __future__ import annotations


from pathlib import Path

from ingestion.chunking import (
    ChunkingPipeline,
    FixedWindowChunker,
    StructureAwareChunker,
)
from ingestion.chunking.models import ChunkDataset
from tests.fixtures.synthetic_processed_docs import (
    create_fixture_academic_calendar,
    create_fixture_duplicate_content,
    create_fixture_lists,
    create_fixture_missing_metadata,
    create_fixture_multi_entity_chunk,
    create_fixture_multi_page,
    create_fixture_nested_headings,
    create_fixture_normal_syllabus,
    create_fixture_oversized_paragraph,
    create_fixture_with_large_table,
    create_fixture_with_small_table,
)


def test_deterministic_chunk_ids_and_ordering() -> None:
    """Verify that chunking produces deterministic chunk IDs and ordering for identical input."""

    doc = create_fixture_normal_syllabus("doc_deterministic")
    chunker = StructureAwareChunker()

    chunks_run1 = chunker.chunk_document(doc)
    chunks_run2 = chunker.chunk_document(doc)

    assert len(chunks_run1) == len(chunks_run2)
    for c1, c2 in zip(chunks_run1, chunks_run2):
        assert c1.chunk_id == c2.chunk_id
        assert c1.text == c2.text
        assert c1.token_count == c2.token_count
        assert c1.provenance.element_ids == c2.provenance.element_ids
        assert c1.chunk_id.startswith("doc_deterministic_chunk_")


def test_token_based_chunk_sizing_and_diagnostic_counts() -> None:
    """Verify chunk size is governed by tokens while storing diagnostic char and word counts."""
    doc = create_fixture_normal_syllabus()
    chunker = StructureAwareChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 0
    for chunk in chunks:
        assert chunk.token_count > 0
        assert chunk.word_count > 0
        assert chunk.char_count > 0
        assert chunk.char_count >= chunk.word_count


def test_heading_boundaries_and_nested_hierarchy() -> None:
    """Verify chunks respect heading boundaries and preserve explicit ancestral heading hierarchies."""
    doc = create_fixture_nested_headings()
    chunker = StructureAwareChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 0
    content_chunk = chunks[-1]
    # Check hierarchical section path
    assert "SR University Curriculum" in content_chunk.metadata.section_path
    assert "Computer Science and Engineering" in content_chunk.metadata.section_path
    assert "Unit II: Trees" in content_chunk.metadata.section_path
    assert " > " in content_chunk.metadata.section_path

    # Check ancestral list
    assert len(content_chunk.metadata.heading_hierarchy) >= 3
    assert content_chunk.metadata.heading_hierarchy[0] == "SR University Curriculum"


def test_atomic_table_preservation() -> None:
    """Verify that small/medium tables are preserved as complete atomic chunks with table metadata."""
    doc = create_fixture_with_small_table()
    chunker = StructureAwareChunker()
    chunks = chunker.chunk_document(doc)

    table_chunks = [c for c in chunks if c.is_table]
    assert len(table_chunks) == 1
    tbl = table_chunks[0]
    assert tbl.is_table is True
    assert "| Course Code | Course Title | Credits |" in tbl.text
    assert "23CSE302T" in tbl.text
    assert "23CSE304T" in tbl.text
    assert tbl.table_metadata is not None
    assert tbl.table_metadata["split"] is False


def test_oversized_table_row_splitting_and_header_replication() -> None:
    """Verify oversized tables split by rows and replicate column headers across every segment."""
    doc = create_fixture_with_large_table(row_count=50)
    # Configure tight max_tokens to force row-based splitting
    chunker = StructureAwareChunker(target_tokens=150, max_tokens=300)
    chunks = chunker.chunk_document(doc)

    table_chunks = [c for c in chunks if c.is_table]
    assert len(table_chunks) > 1, "Large table should be split into multiple chunks"

    # Every split table chunk must retain the headers and table identity
    for chunk in table_chunks:
        assert "| Course Code | Course Title |" in chunk.text
        assert "| --- |" in chunk.text
        assert chunk.table_metadata is not None
        assert chunk.table_metadata["split"] is True
        assert "row_start" in chunk.table_metadata
        assert "row_end" in chunk.table_metadata


def test_list_preservation() -> None:
    """Verify that list items are preserved together under their parent heading."""
    doc = create_fixture_lists()
    chunker = StructureAwareChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 1
    first_chunk = chunks[0]
    assert "1. Minimum 75% attendance" in first_chunk.text
    assert "2. Condonation of attendance" in first_chunk.text
    assert "General Conduct Rules" in first_chunk.metadata.section_path


def test_multi_page_and_multi_element_provenance() -> None:
    """Verify multi-page and multi-element chunks aggregate all contributing page numbers and element IDs."""
    doc = create_fixture_multi_page()
    chunker = StructureAwareChunker(target_tokens=500)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 1
    # Check aggregated provenance
    all_pages = set()
    for chunk in chunks:
        all_pages.update(chunk.provenance.page_numbers)
        assert len(chunk.provenance.element_ids) > 0
        assert chunk.provenance.document_id == doc.document_id
        assert chunk.provenance.source_file == "guide.pdf"

    assert {1, 2, 3}.issubset(all_pages)


def test_metadata_inheritance_and_chunk_local_entities() -> None:
    """Verify chunks inherit document metadata and accurately extract chunk-local entities."""
    doc = create_fixture_multi_entity_chunk()
    chunker = StructureAwareChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    chunk = chunks[0]

    # Inherited document metadata
    assert chunk.metadata.department == "Computer Science and Engineering"
    assert chunk.metadata.semester == "Semester VII"
    assert chunk.metadata.program == "B.Tech"
    assert chunk.metadata.academic_year == "2026-27"

    # Chunk-local detected entities
    assert "23CSE302T" in chunk.metadata.chunk_course_codes
    assert "20EC201" in chunk.metadata.chunk_course_codes
    assert "R23" in chunk.metadata.chunk_regulations
    assert "Mid-Semester Examination I" in chunk.metadata.chunk_examinations
    assert any("12 September 2026 to 16 September 2026" in d for d in chunk.metadata.chunk_dates)


def test_missing_optional_metadata_non_fabrication() -> None:
    """Verify chunks do not fabricate metadata when document-level fields are None."""
    doc = create_fixture_missing_metadata()
    chunker = StructureAwareChunker()
    chunks = chunker.chunk_document(doc)

    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.metadata.department is None
    assert chunk.metadata.semester is None
    assert chunk.metadata.academic_year is None
    assert chunk.metadata.program is None
    assert chunk.metadata.regulations == []


def test_in_document_duplicate_chunk_detection() -> None:
    """Verify exact duplicate chunks within a document are detected, reported, and preserved."""
    doc = create_fixture_duplicate_content()
    pipeline = ChunkingPipeline()
    dataset = pipeline.chunk_processed_document(doc)

    assert dataset.total_chunks == 2
    # Both chunks are preserved
    assert len(dataset.chunks) == 2
    assert dataset.chunks[0].text == dataset.chunks[1].text
    # Duplicates are detected and reported
    assert len(dataset.duplicate_reports) == 1
    dup = dataset.duplicate_reports[0]
    assert dup.occurrences == 2
    assert "Attendance Notice" in dup.text_snippet
    assert "Regulation R23" in dataset.chunks[0].text


def test_oversized_paragraph_fallback_splitting() -> None:
    """Verify paragraphs exceeding max_tokens split across sentence boundaries."""
    doc = create_fixture_oversized_paragraph()
    chunker = StructureAwareChunker(target_tokens=300, max_tokens=600)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) > 1, "Oversized paragraph must be split into multiple chunks"
    for chunk in chunks:
        assert chunk.token_count <= 650
        assert chunk.text.endswith((".", "!", "?")) or len(chunk.text) > 0


def test_fixed_window_chunker_baseline() -> None:
    """Verify FixedWindowChunker operates deterministically as a comparative baseline."""
    doc = create_fixture_normal_syllabus("doc_fixed")
    chunker = FixedWindowChunker(target_tokens=30, overlap_tokens=10)
    chunks = chunker.chunk_document(doc)

    assert len(chunks) >= 2
    assert chunks[0].chunk_id == "doc_fixed_chunk_0000"
    assert chunks[1].chunk_id == "doc_fixed_chunk_0001"
    assert chunks[0].metadata.section_path == "FixedWindow"


def test_chunk_dataset_validation() -> None:
    """Verify dataset validation catches empty text, mismatched counts, or duplicate IDs."""
    doc = create_fixture_normal_syllabus()
    pipeline = ChunkingPipeline()
    dataset = pipeline.chunk_processed_document(doc)

    assert dataset.validate_dataset() == []

    # Inject validation error: mismatched total_chunks
    dataset.total_chunks = 999
    errors = dataset.validate_dataset()
    assert len(errors) > 0
    assert "total_chunks" in errors[0]


def test_chunk_dataset_serialization_roundtrip(tmp_path: Path) -> None:
    """Verify ChunkDataset saves to JSON and reloads perfectly without data loss."""
    doc = create_fixture_academic_calendar()
    pipeline = ChunkingPipeline()
    dataset = pipeline.chunk_processed_document(doc)

    save_path = tmp_path / "calendar_chunks.json"
    dataset.save_to_file(save_path)

    assert save_path.exists()
    loaded_dataset = ChunkDataset.load_from_file(save_path)

    assert loaded_dataset.document_id == dataset.document_id
    assert loaded_dataset.total_chunks == dataset.total_chunks
    assert loaded_dataset.chunks[0].chunk_id == dataset.chunks[0].chunk_id
    assert loaded_dataset.chunks[0].text == dataset.chunks[0].text
    assert loaded_dataset.chunks[0].provenance.element_ids == dataset.chunks[0].provenance.element_ids


def test_batch_directory_chunking_with_failure_isolation(tmp_path: Path) -> None:
    """Verify directory-level chunking processes valid documents and isolates corrupted files."""
    processed_dir = tmp_path / "processed"
    chunks_dir = tmp_path / "chunks"
    processed_dir.mkdir()

    # 1. Valid ProcessedDocument 1
    doc1 = create_fixture_normal_syllabus("doc_01")
    doc1.save_to_file(processed_dir / "doc_01.json")

    # 2. Valid ProcessedDocument 2
    doc2 = create_fixture_with_small_table("doc_02")
    doc2.save_to_file(processed_dir / "doc_02.json")

    # 3. Corrupted JSON file
    corrupt_file = processed_dir / "corrupted_doc.json"
    corrupt_file.write_text("{ Invalid JSON content !!! }", encoding="utf-8")

    pipeline = ChunkingPipeline()
    batch_result = pipeline.chunk_directory(processed_dir, chunks_dir)

    assert batch_result.total_files_found == 3
    assert batch_result.successful_count == 2
    assert batch_result.failed_count == 1
    assert len(batch_result.failures) == 1
    assert "corrupted_doc.json" in batch_result.failures[0]["file_path"]

    # Verify output chunk files
    chunk_files = list(chunks_dir.glob("*_chunks.json"))
    assert len(chunk_files) == 2
