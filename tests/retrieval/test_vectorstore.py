"""Unit tests for SQLiteVectorStore persistence, similarity scoring, filtering, and manifest."""

import numpy as np
import pytest

from retrieval.models import IndexCompatibilityError, IndexManifest, VectorRecord
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


@pytest.fixture
def memory_store():
    """Return an in-memory SQLiteVectorStore instance for isolated fast testing."""
    return SQLiteVectorStore(db_path=":memory:")


def _create_record(
    chunk_id: str,
    vector: list[float],
    text: str = "sample text",
    department: str = "CSE",
    semester: str = "VII",
    regulation: str = "R23",
    doc_type: str = "syllabus",
) -> VectorRecord:
    return VectorRecord(
        chunk_id=chunk_id,
        document_id="doc_test_123",
        text=text,
        chunk_content_hash="dummy_hash",
        vector=vector,
        metadata={
            "department": department,
            "semester": semester,
            "regulation": regulation,
            "document_type": doc_type,
        },
        provenance={"source_path": "test.pdf", "page_start": 1, "page_end": 1},
    )


class TestSQLiteVectorStoreBasics:
    """Test core storage operations: add, get, count, delete, clear."""

    def test_empty_store_state(self, memory_store):
        assert memory_store.count() == 0
        assert memory_store.get_record("nonexistent") is None
        assert memory_store.get_manifest() is None
        # Empty search returns empty list safely
        assert memory_store.search(query_vector=[1.0, 0.0], top_k=5) == []

    def test_add_and_get_record(self, memory_store):
        rec = _create_record("chk_1", [0.6, 0.8])
        added = memory_store.add_records([rec])
        assert added == 1
        assert memory_store.count() == 1

        fetched = memory_store.get_record("chk_1")
        assert fetched is not None
        assert fetched.chunk_id == "chk_1"
        assert fetched.metadata["department"] == "CSE"
        assert np.allclose(fetched.vector, [0.6, 0.8], atol=1e-5)

    def test_delete_records(self, memory_store):
        recs = [_create_record("chk_1", [1.0, 0.0]), _create_record("chk_2", [0.0, 1.0])]
        memory_store.add_records(recs)
        assert memory_store.count() == 2

        deleted = memory_store.delete_records(["chk_1"])
        assert deleted == 1
        assert memory_store.count() == 1
        assert memory_store.get_record("chk_1") is None
        assert memory_store.get_record("chk_2") is not None

    def test_clear_records(self, memory_store):
        recs = [_create_record("chk_1", [1.0, 0.0]), _create_record("chk_2", [0.0, 1.0])]
        memory_store.add_records(recs)
        memory_store.clear()
        assert memory_store.count() == 0


class TestCosineSimilarityAndScoring:
    """Verify raw cosine similarity in [-1, 1] and normalized score in [0, 1]."""

    def test_exact_match_score(self, memory_store):
        # Query == Record vector -> cosine = 1.0, normalized = 1.0
        rec = _create_record("chk_ident", [1.0, 0.0])
        memory_store.add_records([rec])

        results = memory_store.search(query_vector=[1.0, 0.0], top_k=1)
        assert len(results) == 1
        assert pytest.approx(results[0].cosine_similarity, abs=1e-5) == 1.0
        assert pytest.approx(results[0].normalized_score, abs=1e-5) == 1.0
        assert pytest.approx(results[0].score, abs=1e-5) == 1.0

    def test_orthogonal_vector_score(self, memory_store):
        # Query [0, 1] vs Record [1, 0] -> cosine = 0.0, normalized = 0.5
        rec = _create_record("chk_ortho", [1.0, 0.0])
        memory_store.add_records([rec])

        results = memory_store.search(query_vector=[0.0, 1.0], top_k=1)
        assert len(results) == 1
        assert pytest.approx(results[0].cosine_similarity, abs=1e-5) == 0.0
        assert pytest.approx(results[0].normalized_score, abs=1e-5) == 0.5

    def test_opposite_vector_score(self, memory_store):
        # Query [-1, 0] vs Record [1, 0] -> cosine = -1.0, normalized = 0.0
        rec = _create_record("chk_opp", [1.0, 0.0])
        memory_store.add_records([rec])

        results = memory_store.search(query_vector=[-1.0, 0.0], top_k=1)
        assert len(results) == 1
        assert pytest.approx(results[0].cosine_similarity, abs=1e-5) == -1.0
        assert pytest.approx(results[0].normalized_score, abs=1e-5) == 0.0


class TestSearchDeterminismAndTopK:
    """Verify deterministic tie-breaking and top_k bounds."""

    def test_tie_breaking_order(self, memory_store):
        # Three records with identical similarity to query [1.0, 0.0]
        recs = [
            _create_record("chk_z", [1.0, 0.0]),
            _create_record("chk_a", [1.0, 0.0]),
            _create_record("chk_m", [1.0, 0.0]),
        ]
        memory_store.add_records(recs)

        results = memory_store.search(query_vector=[1.0, 0.0], top_k=3)
        assert len(results) == 3
        # Should tie-break by chunk_id ascending: chk_a, chk_m, chk_z
        assert [r.chunk_id for r in results] == ["chk_a", "chk_m", "chk_z"]

    def test_top_k_bounds(self, memory_store):
        recs = [_create_record(f"chk_{i}", [1.0, 0.0]) for i in range(10)]
        memory_store.add_records(recs)

        # top_k=3 returns exactly 3
        assert len(memory_store.search([1.0, 0.0], top_k=3)) == 3
        # top_k=20 when only 10 exist returns 10
        assert len(memory_store.search([1.0, 0.0], top_k=20)) == 10

    def test_invalid_top_k_raises(self, memory_store):
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            memory_store.search([1.0, 0.0], top_k=0)
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            memory_store.search([1.0, 0.0], top_k=-2)


class TestMetadataFiltering:
    """Verify SQL metadata pre-filtering."""

    def test_single_and_multiple_filters(self, memory_store):
        recs = [
            _create_record("chk_cse_7", [1.0, 0.0], department="CSE", semester="VII"),
            _create_record("chk_cse_5", [1.0, 0.0], department="CSE", semester="V"),
            _create_record("chk_ece_7", [1.0, 0.0], department="ECE", semester="VII"),
        ]
        memory_store.add_records(recs)

        # Filter by department
        res_cse = memory_store.search([1.0, 0.0], top_k=10, filters={"department": "CSE"})
        assert len(res_cse) == 2
        assert {r.chunk_id for r in res_cse} == {"chk_cse_7", "chk_cse_5"}

        # Multiple filters: department + semester
        res_cse_7 = memory_store.search(
            [1.0, 0.0], top_k=10, filters={"department": "CSE", "semester": "VII"}
        )
        assert len(res_cse_7) == 1
        assert res_cse_7[0].chunk_id == "chk_cse_7"

    def test_filter_no_matches_returns_empty_list(self, memory_store):
        rec = _create_record("chk_1", [1.0, 0.0], department="CSE")
        memory_store.add_records([rec])

        res = memory_store.search([1.0, 0.0], top_k=5, filters={"department": "CIVIL"})
        assert res == []


class TestPersistenceAndManifest:
    """Verify file-based SQLite persistence across reloads and manifest compatibility."""

    def test_persistence_across_reloads(self, tmp_path):
        db_file = str(tmp_path / "test_persist.db")

        # Session 1: write record and manifest
        store1 = SQLiteVectorStore(db_path=db_file)
        manifest = IndexManifest(
            embedding_provider="fasthash",
            embedding_model="fasthash-384",
            embedding_dimension=2,
            distance_metric="cosine",
            index_version="1.0.0",
        )
        store1.save_manifest(manifest)
        store1.add_records([_create_record("chk_saved", [0.6, 0.8])])
        assert store1.count() == 1

        # Session 2: open new instance on same file
        store2 = SQLiteVectorStore(db_path=db_file)
        assert store2.count() == 1
        rec = store2.get_record("chk_saved")
        assert rec is not None
        assert np.allclose(rec.vector, [0.6, 0.8], atol=1e-5)

        saved_manifest = store2.get_manifest()
        assert saved_manifest is not None
        assert saved_manifest.embedding_provider == "fasthash"
        assert saved_manifest.embedding_dimension == 2

    def test_manifest_compatibility_validation(self, memory_store):
        manifest = IndexManifest(
            embedding_provider="fasthash",
            embedding_model="fasthash-384",
            embedding_dimension=384,
            distance_metric="cosine",
            index_version="1.0.0",
            total_vectors=5,
        )
        memory_store.save_manifest(manifest)

        # Compatible query passes silently
        memory_store.validate_manifest_compatibility("fasthash", "fasthash-384", 384)

        # Incompatible dimension raises IndexCompatibilityError
        with pytest.raises(IndexCompatibilityError, match="Dimension mismatch"):
            memory_store.validate_manifest_compatibility("fasthash", "fasthash-384", 768)

        # Incompatible model raises IndexCompatibilityError
        with pytest.raises(IndexCompatibilityError, match="Model mismatch"):
            memory_store.validate_manifest_compatibility("ollama", "nomic-embed-text", 384)
