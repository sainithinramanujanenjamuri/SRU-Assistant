"""Comprehensive unit tests for BM25Index, BM25Retriever, and BM25Indexer."""

from pathlib import Path

import pytest

from ingestion.chunking.models import Chunk, ChunkMetadata, ChunkProvenance
from retrieval.lexical.bm25 import BM25Index, BM25Retriever
from retrieval.lexical.indexer import BM25Indexer
from retrieval.models import (
    BM25CorruptionError,
    BM25IndexError,
    IndexCompatibilityError,
)


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    return [
        Chunk(
            chunk_id="chunk_001",
            document_id="doc_syllabus_23cse302t",
            text="Course 23CSE302T covers fundamental data structures, binary search trees, and tree traversals.",
            chunk_index=0,
            token_count=16,
            char_count=90,
            word_count=13,
            metadata=ChunkMetadata(
                document_id="doc_syllabus_23cse302t",
                document_name="syllabus_23cse302t.pdf",
                department="Computer Science and Engineering",
                semester="III",
                academic_year="2026-27",
                document_type="syllabus",
            ),
            provenance=ChunkProvenance(
                document_id="doc_syllabus_23cse302t",
                source_file="syllabus_23cse302t.pdf",
                page_numbers=[1],
            ),
        ),
        Chunk(
            chunk_id="chunk_002",
            document_id="doc_syllabus_23cse302t",
            text="Learning outcomes for 23CSE302T include asymptotic complexity analysis and graph algorithms.",
            chunk_index=1,
            token_count=14,
            char_count=93,
            word_count=12,
            metadata=ChunkMetadata(
                document_id="doc_syllabus_23cse302t",
                document_name="syllabus_23cse302t.pdf",
                department="Computer Science and Engineering",
                semester="III",
                academic_year="2026-27",
                document_type="syllabus",
            ),
            provenance=ChunkProvenance(
                document_id="doc_syllabus_23cse302t",
                source_file="syllabus_23cse302t.pdf",
                page_numbers=[1],
            ),
        ),
        Chunk(
            chunk_id="chunk_003",
            document_id="doc_calendar_2026_27",
            text="Academic Calendar 2026-27: Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026.",
            chunk_index=0,
            token_count=19,
            char_count=113,
            word_count=16,
            metadata=ChunkMetadata(
                document_id="doc_calendar_2026_27",
                document_name="academic_calendar.pdf",
                department="University Wide",
                semester="All",
                academic_year="2026-27",
                document_type="academic_calendar",
            ),
            provenance=ChunkProvenance(
                document_id="doc_calendar_2026_27",
                source_file="academic_calendar.pdf",
                page_numbers=[1],
            ),
        ),
    ]


# ==============================================================================
# BM25 Mathematical & Scoring Tests
# ==============================================================================


def test_bm25_idf_is_strictly_positive():
    """Robertson/Spärck Jones formula guarantees strictly positive IDF for any term in corpus."""
    index = BM25Index()
    index.add_or_update_chunk("c1", "d1", "algorithms data structures", "hash1")
    index.add_or_update_chunk("c2", "d1", "algorithms tree traversals", "hash2")

    idf_common = index.compute_idf("algorithms")  # df = 2, N = 2
    idf_rare = index.compute_idf("structures")   # df = 1, N = 2

    assert idf_common > 0.0
    assert idf_rare > idf_common


def test_bm25_exact_course_code_retrieval(sample_chunks: list[Chunk]):
    """Querying exact course code 23CSE302T should rank syllabus chunks at top."""
    index = BM25Index()
    for chk in sample_chunks:
        index.add_or_update_chunk(
            chk.chunk_id, chk.document_id, chk.text, "hash_" + chk.chunk_id,
            chk.metadata.model_dump(), chk.provenance.model_dump()
        )

    retriever = BM25Retriever(index)
    results = retriever.search("23CSE302T", top_k=5)

    assert len(results) >= 2
    retrieved_ids = [r.chunk_id for r in results]
    assert "chunk_001" in retrieved_ids
    assert "chunk_002" in retrieved_ids
    assert "chunk_003" not in retrieved_ids  # Calendar chunk does not mention 23CSE302T


def test_bm25_date_and_hyphen_retrieval(sample_chunks: list[Chunk]):
    """Querying dates or hyphenated sessions should retrieve the calendar chunk."""
    index = BM25Index()
    for chk in sample_chunks:
        index.add_or_update_chunk(
            chk.chunk_id, chk.document_id, chk.text, "hash_" + chk.chunk_id,
            chk.metadata.model_dump(), chk.provenance.model_dump()
        )

    retriever = BM25Retriever(index)
    results = retriever.search("12 September 2026 Mid-Semester", top_k=2)

    assert len(results) > 0
    assert results[0].chunk_id == "chunk_003"
    assert results[0].bm25_score > 0.0


def test_bm25_score_normalization_and_tie_breaking(sample_chunks: list[Chunk]):
    """Normalized score must be in [0.0, 1.0], and ties must break deterministically by chunk_id."""
    index = BM25Index()
    # Insert two chunks with identical text
    index.add_or_update_chunk("chunk_B", "doc1", "identical text content", "hashB")
    index.add_or_update_chunk("chunk_A", "doc1", "identical text content", "hashA")

    retriever = BM25Retriever(index)
    results = retriever.search("identical text", top_k=2)

    assert len(results) == 2
    assert results[0].bm25_score == results[1].bm25_score
    # Chunk A comes before Chunk B alphabetically
    assert results[0].chunk_id == "chunk_A"
    assert results[1].chunk_id == "chunk_B"
    # Identical score edge case produces 1.0 without ZeroDivisionError
    assert results[0].normalized_score == 1.0
    assert results[1].normalized_score == 1.0


def test_bm25_metadata_filtering(sample_chunks: list[Chunk]):
    """Filtering should constrain results before ranking."""
    index = BM25Index()
    for chk in sample_chunks:
        index.add_or_update_chunk(
            chk.chunk_id, chk.document_id, chk.text, "hash_" + chk.chunk_id,
            chk.metadata.model_dump(), chk.provenance.model_dump()
        )

    retriever = BM25Retriever(index)

    # Filter to syllabus only
    res_syllabus = retriever.search("2026", filters={"document_type": "syllabus"})
    assert all(r.metadata.get("document_type") == "syllabus" for r in res_syllabus)

    # Filter to calendar only
    res_calendar = retriever.search("2026", filters={"document_type": "academic_calendar"})
    assert len(res_calendar) == 1
    assert res_calendar[0].chunk_id == "chunk_003"

    # Filter with no matches
    res_empty = retriever.search("2026", filters={"department": "Mechanical Engineering"})
    assert res_empty == []


def test_bm25_edge_cases():
    """Empty corpus, empty query, stop words only, unknown terms."""
    index = BM25Index()
    retriever = BM25Retriever(index)

    # Empty corpus
    assert retriever.search("test query") == []

    # Populate one chunk
    index.add_or_update_chunk("c1", "d1", "computer science engineering", "h1")

    # Empty query raises ValueError
    with pytest.raises(ValueError):
        retriever.search("")

    with pytest.raises(ValueError):
        retriever.search("   ")

    # top_k <= 0 raises ValueError
    with pytest.raises(ValueError):
        retriever.search("query", top_k=0)

    # Query with only stop words returns empty list safely
    assert retriever.search("the and is") == []

    # Query with terms not in vocabulary returns empty list safely
    assert retriever.search("astrophysics quantum") == []


# ==============================================================================
# Persistence, Manifest & Corruption Tests
# ==============================================================================


def test_bm25_persistence_and_compatibility(tmp_path: Path):
    """Index save and load round-trip with manifest validation."""
    save_file = tmp_path / "test_bm25.json"

    index = BM25Index(k1=1.5, b=0.75)
    index.add_or_update_chunk("c1", "d1", "algorithms and data structures", "h1")
    index.save(save_file)

    assert save_file.exists()

    # Load with compatible parameters
    loaded_index = BM25Index(k1=1.5, b=0.75)
    loaded_index.load(save_file)
    assert loaded_index.total_chunks == 1
    assert "c1" in loaded_index.doc_records

    # Incompatible k1 raises IndexCompatibilityError
    incompatible_index = BM25Index(k1=2.0, b=0.75)
    with pytest.raises(IndexCompatibilityError):
        incompatible_index.load(save_file)


def test_bm25_corruption_handling(tmp_path: Path):
    """Missing or corrupted index files must raise appropriate exceptions."""
    missing_file = tmp_path / "nonexistent.json"
    index = BM25Index()

    with pytest.raises(BM25IndexError):
        index.load(missing_file)

    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(BM25CorruptionError):
        index.load(corrupt_file)


# ==============================================================================
# BM25Indexer Delta State Tests
# ==============================================================================


def test_bm25_indexer_delta_lifecycle(tmp_path: Path, sample_chunks: list[Chunk]):
    """Indexer must accurately track UNCHANGED, MODIFIED, NEW, and REMOVED chunks."""
    index_file = tmp_path / "lifecycle_bm25.json"
    indexer = BM25Indexer(index_path=index_file)

    # Run 1: Index 2 chunks (NEW)
    rep1 = indexer.index_chunks(sample_chunks[:2])
    assert rep1.chunks_requested == 2
    assert rep1.chunks_indexed == 2
    assert rep1.chunks_skipped == 0

    # Run 2: Re-index identical chunks (UNCHANGED / Idempotent)
    rep2 = indexer.index_chunks(sample_chunks[:2])
    assert rep2.chunks_indexed == 0
    assert rep2.chunks_skipped == 2

    # Run 3: Modify chunk text (MODIFIED) + Add 1 chunk (NEW)
    modified_text = "Updated content for 23CSE302T with advanced graph theory."
    modified_chunk = Chunk(
        chunk_id=sample_chunks[0].chunk_id,
        document_id=sample_chunks[0].document_id,
        text=modified_text,
        chunk_index=0,
        token_count=10,
        char_count=len(modified_text),
        word_count=len(modified_text.split()),
        metadata=sample_chunks[0].metadata,
        provenance=sample_chunks[0].provenance,
    )
    rep3 = indexer.index_chunks([modified_chunk, sample_chunks[1], sample_chunks[2]])
    assert rep3.chunks_updated == 1  # modified chunk
    assert rep3.chunks_skipped == 1  # unchanged chunk_002
    assert rep3.chunks_indexed == 1  # new chunk_003

    # Run 4: Remove a chunk by submitting only chunk_001
    rep4 = indexer.index_chunks([modified_chunk])
    assert rep4.chunks_skipped == 1
    assert rep4.chunks_removed == 2  # chunk_002 and chunk_003 removed
    assert indexer.index.total_chunks == 1
