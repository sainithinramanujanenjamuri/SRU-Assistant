"""Unit tests for VectorIndexer idempotency, stale-chunk updates, and batching."""

from ingestion.chunking.models import Chunk, ChunkMetadata, ChunkProvenance
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.vectorstore.indexer import VectorIndexer
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


def _make_chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=chunk_id,
        document_id="doc_test_abc",
        chunk_index=0,
        text=text,
        token_count=100,
        char_count=len(text),
        word_count=len(text.split()),
        metadata=ChunkMetadata(
            document_id="doc_test_abc",
            document_name="test_syllabus.pdf",
            document_type=".pdf",
            department="CSE",
            semester="VII",
            regulations=["R23"],
            category="syllabus",
        ),
        provenance=ChunkProvenance(
            document_id="doc_test_abc",
            source_file="test_syllabus.pdf",
            page_numbers=[1],
            line_numbers=[],
            element_ids=["elem_1"],
        ),
    )


class TestVectorIndexer:
    """Test idempotency and stale chunk detection."""

    def test_first_run_indexes_all_chunks(self):
        store = SQLiteVectorStore(db_path=":memory:")
        model = FastHashEmbeddingModel(dimension=64)
        indexer = VectorIndexer(embedding_model=model, vector_store=store)

        chunks = [
            _make_chunk("c1", "Introduction to Algorithms and Data Structures"),
            _make_chunk("c2", "Sorting: QuickSort, MergeSort, HeapSort"),
        ]
        report = indexer.index_chunks(chunks, batch_size=10)

        assert report.chunks_requested == 2
        assert report.chunks_indexed == 2
        assert report.chunks_skipped == 0
        assert report.chunks_updated == 0
        assert report.chunks_failed == 0
        assert store.count() == 2

    def test_idempotent_reindexing_skips_unchanged_chunks(self):
        store = SQLiteVectorStore(db_path=":memory:")
        model = FastHashEmbeddingModel(dimension=64)
        indexer = VectorIndexer(embedding_model=model, vector_store=store)

        chunks = [
            _make_chunk("c1", "Introduction to Algorithms and Data Structures"),
            _make_chunk("c2", "Sorting: QuickSort, MergeSort, HeapSort"),
        ]
        # First index run
        indexer.index_chunks(chunks, batch_size=10)

        # Second index run with exact same chunks
        report2 = indexer.index_chunks(chunks, batch_size=10)

        assert report2.chunks_requested == 2
        assert report2.chunks_indexed == 0
        assert report2.chunks_skipped == 2
        assert report2.chunks_updated == 0
        assert store.count() == 2

    def test_stale_chunk_detection_and_update(self):
        store = SQLiteVectorStore(db_path=":memory:")
        model = FastHashEmbeddingModel(dimension=64)
        indexer = VectorIndexer(embedding_model=model, vector_store=store)

        chunks = [_make_chunk("c1", "Original text content about examinations")]
        indexer.index_chunks(chunks)

        # Modify chunk text for c1
        modified_chunks = [_make_chunk("c1", "Updated text content with new exam dates")]
        report = indexer.index_chunks(modified_chunks)

        assert report.chunks_requested == 1
        assert report.chunks_indexed == 0
        assert report.chunks_updated == 1
        assert report.chunks_skipped == 0
        assert store.count() == 1

        rec = store.get_record("c1")
        assert rec is not None
        assert "Updated text content" in rec.text

    def test_batching_multiple_slices(self):
        store = SQLiteVectorStore(db_path=":memory:")
        model = FastHashEmbeddingModel(dimension=64)
        indexer = VectorIndexer(embedding_model=model, vector_store=store)

        # 7 chunks with batch size 3 -> 3 batches (3, 3, 1)
        chunks = [_make_chunk(f"c_{i}", f"Academic text chunk number {i}") for i in range(7)]
        report = indexer.index_chunks(chunks, batch_size=3)

        assert report.chunks_requested == 7
        assert report.chunks_indexed == 7
        assert store.count() == 7
