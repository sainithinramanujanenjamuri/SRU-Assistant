"""Integration and failure-injection test suite for transactional ingestion and rollback recovery."""
from __future__ import annotations

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.query_service import IngestionStageError, RAGQueryService

client = TestClient(app)


def test_failure_injection_at_chunking_stage_rolls_back_artifacts(tmp_path: Path, monkeypatch) -> None:
    """Verify that failure during chunking removes intermediate processed JSON files."""
    service = RAGQueryService.get_instance()
    initial_vec_count = service.vector_store.count()
    initial_bm25_count = len(service.bm25_retriever.index.doc_records)

    test_file = tmp_path / "stage2_fail.txt"
    test_file.write_text("SR University Test Circular for Stage 2 Failure Injection.\nValid content for testing.", encoding="utf-8")

    # Inject failure into ChunkingPipeline.chunk_processed_document
    from ingestion.chunking.pipeline import ChunkingPipeline
    def mock_chunk_fail(self, doc):
        raise ValueError("Simulated Stage 2 Chunking Failure")

    monkeypatch.setattr(ChunkingPipeline, "chunk_processed_document", mock_chunk_fail)

    with pytest.raises(IngestionStageError) as exc_info:
        service.ingest_and_index_file(test_file)

    assert "chunking" in exc_info.value.stage

    # Verify no orphan chunks or vector changes
    assert service.vector_store.count() == initial_vec_count
    assert len(service.bm25_retriever.index.doc_records) == initial_bm25_count


def test_failure_injection_at_vector_indexing_stage_rolls_back(tmp_path: Path, monkeypatch) -> None:
    """Verify that failure during vector indexing removes chunk datasets and intermediate files."""
    service = RAGQueryService.get_instance()
    initial_vec_count = service.vector_store.count()
    initial_bm25_count = len(service.bm25_retriever.index.doc_records)

    test_file = tmp_path / "stage3_fail.txt"
    test_file.write_text("SR University Test Circular for Stage 3 Failure Injection.\nContent line two.", encoding="utf-8")

    # Inject failure into VectorIndexer.index_chunks
    from retrieval.vectorstore.indexer import VectorIndexer
    def mock_vec_fail(self, chunks, batch_size=32):
        raise RuntimeError("Simulated Stage 3 SQLite Vector Store Write Failure")

    monkeypatch.setattr(VectorIndexer, "index_chunks", mock_vec_fail)

    with pytest.raises(IngestionStageError) as exc_info:
        service.ingest_and_index_file(test_file)

    assert "vector_indexing" in exc_info.value.stage

    # Verify state remains synchronized
    assert service.vector_store.count() == initial_vec_count
    assert len(service.bm25_retriever.index.doc_records) == initial_bm25_count


def test_failure_injection_at_bm25_stage_rolls_back_vector_records(tmp_path: Path, monkeypatch) -> None:
    """Verify that failure during BM25 indexing cleans up vector records and preserves store sync."""
    service = RAGQueryService.get_instance()
    initial_vec_count = service.vector_store.count()
    initial_bm25_count = len(service.bm25_retriever.index.doc_records)

    test_file = tmp_path / "stage4_fail.txt"
    test_file.write_text("SR University Test Circular for Stage 4 Failure Injection.\nEnsuring dual-store sync rollback.", encoding="utf-8")

    # Inject failure into BM25Indexer.index_chunks
    from retrieval.lexical.indexer import BM25Indexer
    def mock_bm25_fail(self, chunks, force_rebuild=False, prune_missing=True):
        raise IOError("Simulated Stage 4 BM25 Inverted Index Disk Full Error")

    monkeypatch.setattr(BM25Indexer, "index_chunks", mock_bm25_fail)

    with pytest.raises(IngestionStageError) as exc_info:
        service.ingest_and_index_file(test_file)

    assert "bm25_indexing" in exc_info.value.stage

    # Dual stores must remain exactly synchronized and unmodified
    assert service.vector_store.count() == initial_vec_count
    assert len(service.bm25_retriever.index.doc_records) == initial_bm25_count


def test_oversized_upload_bounded_streaming_rejection() -> None:
    """Verify that uploading content exceeding the configured boundary is rejected via streaming."""
    service = RAGQueryService.get_instance()
    # Temporarily set max_size_bytes to small threshold to test bounded read rejection
    orig_max = service.document_guard.max_size_bytes
    try:
        service.document_guard.max_size_bytes = 1024  # 1 KB limit
        oversized_content = b"A" * 2048  # 2 KB payload
        files = {"file": ("oversized_notice.txt", io.BytesIO(oversized_content), "text/plain")}

        res = client.post("/api/documents/upload", files=files)
        assert res.status_code == 400
        assert "exceeds maximum permitted size" in res.json()["detail"]
    finally:
        service.document_guard.max_size_bytes = orig_max

