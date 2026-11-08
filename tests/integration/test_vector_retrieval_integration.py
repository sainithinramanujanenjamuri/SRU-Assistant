"""Integration test for full end-to-end vector indexing and semantic retrieval pipeline."""

import pytest

from ingestion.chunking.structure_aware import StructureAwareChunker
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.vectorstore.indexer import VectorIndexer
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore
from tests.fixtures.synthetic_processed_docs import (
    create_fixture_academic_calendar,
    create_fixture_normal_syllabus,
    create_fixture_with_small_table,
)


@pytest.fixture
def integrated_vector_system(tmp_path):
    """Build a complete end-to-end pipeline from processed documents to indexed vector store."""
    db_path = str(tmp_path / "integrated_vectors.db")
    store = SQLiteVectorStore(db_path=db_path)
    model = FastHashEmbeddingModel(dimension=384)
    indexer = VectorIndexer(embedding_model=model, vector_store=store)
    chunker = StructureAwareChunker(target_tokens=300, overlap_tokens=50)

    # Ingest 3 distinct synthetic academic documents
    docs = [
        create_fixture_normal_syllabus("doc_syllabus"),
        create_fixture_with_small_table("doc_courses"),
        create_fixture_academic_calendar("doc_calendar"),
    ]

    all_chunks = []
    for doc in docs:
        doc_chunks = chunker.chunk_document(doc)
        all_chunks.extend(doc_chunks)

    # Index all chunks
    report = indexer.index_chunks(all_chunks)
    assert report.chunks_indexed == len(all_chunks)
    assert report.chunks_failed == 0

    retriever = VectorRetriever(embedding_model=model, vector_store=store)
    return {
        "store": store,
        "retriever": retriever,
        "model": model,
        "db_path": db_path,
        "total_chunks": len(all_chunks),
    }


class TestVectorRetrievalIntegration:
    """End-to-end integration tests connecting chunking, indexing, and retrieval."""

    def test_pipeline_indexed_count_and_manifest(self, integrated_vector_system):
        store = integrated_vector_system["store"]
        total = integrated_vector_system["total_chunks"]
        assert store.count() == total
        manifest = store.get_manifest()
        assert manifest is not None
        assert manifest.embedding_provider == "fasthash"
        assert manifest.embedding_dimension == 384
        assert manifest.total_vectors == total

    def test_semantic_query_retrieves_relevant_chunks(self, integrated_vector_system):
        retriever = integrated_vector_system["retriever"]

        # Query 1: Syllabus & learning objectives
        results = retriever.search("What are the learning objectives and algorithms for 23CSE302T?", top_k=3)
        assert len(results) > 0
        top = results[0]
        assert top.document_id == "doc_syllabus"
        assert -1.0 <= top.cosine_similarity <= 1.0
        assert 0.0 <= top.normalized_score <= 1.0
        assert "Learning Objectives" in top.metadata.get("section_path", "") or "Learning Objectives" in top.text

    def test_course_table_retrieval_and_metadata_filter(self, integrated_vector_system):
        retriever = integrated_vector_system["retriever"]

        # Search with department filter
        results = retriever.search(
            "Which courses are listed in the Semester VII course table?",
            top_k=5,
            filters={"department": "Computer Science and Engineering"},
        )
        assert len(results) > 0
        for r in results:
            assert r.metadata.get("department") == "Computer Science and Engineering"
            assert r.document_id in ("doc_syllabus", "doc_courses")

    def test_idempotent_reindex_does_not_duplicate(self, integrated_vector_system):
        store = integrated_vector_system["store"]
        model = integrated_vector_system["model"]
        indexer = VectorIndexer(embedding_model=model, vector_store=store)

        doc = create_fixture_normal_syllabus("doc_syllabus")
        chunker = StructureAwareChunker(target_tokens=300)
        doc_chunks = chunker.chunk_document(doc)

        report = indexer.index_chunks(doc_chunks)
        assert report.chunks_indexed == 0
        assert report.chunks_skipped == len(doc_chunks)
        assert store.count() == integrated_vector_system["total_chunks"]

    def test_reload_persistence_integrity(self, integrated_vector_system):
        db_path = integrated_vector_system["db_path"]
        model = integrated_vector_system["model"]

        # Open completely fresh store instance from disk
        fresh_store = SQLiteVectorStore(db_path=db_path)
        fresh_retriever = VectorRetriever(embedding_model=model, vector_store=fresh_store)

        assert fresh_store.count() == integrated_vector_system["total_chunks"]
        results = fresh_retriever.search("Academic calendar and Dussehra vacation dates", top_k=2)
        assert len(results) > 0
        assert results[0].document_id == "doc_calendar"
