"""Unit tests for VectorRetriever query validation, manifest checks, and search execution."""

import pytest

from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.models import IndexCompatibilityError, IndexManifest, VectorRecord
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


@pytest.fixture
def populated_retriever():
    store = SQLiteVectorStore(db_path=":memory:")
    model = FastHashEmbeddingModel(dimension=64)

    # Initialize manifest
    store.save_manifest(
        IndexManifest(
            embedding_provider=model.provider_name,
            embedding_model=model.model_name,
            embedding_dimension=model.dimension,
            distance_metric="cosine",
            total_vectors=2,
        )
    )

    t1 = "Mid-Semester Examination-I for VII semester CSE commences September 12"
    t2 = "Regulation R23: Minimum 75% attendance required in aggregate"

    recs = [
        VectorRecord(
            chunk_id="chk_exam",
            document_id="doc_exam",
            text=t1,
            chunk_content_hash="h1",
            vector=model.embed_text(t1),
            metadata={"department": "CSE", "semester": "VII", "document_type": "exam_schedule"},
            provenance={"source_path": "exam.pdf", "page_start": 1, "page_end": 1},
        ),
        VectorRecord(
            chunk_id="chk_att",
            document_id="doc_att",
            text=t2,
            chunk_content_hash="h2",
            vector=model.embed_text(t2),
            metadata={"regulation": "R23", "document_type": "academic_regulations"},
            provenance={"source_path": "regs.pdf", "page_start": 3, "page_end": 3},
        ),
    ]
    store.add_records(recs)
    return VectorRetriever(embedding_model=model, vector_store=store)


class TestVectorRetriever:
    """Test retrieval interface and boundary cases."""

    def test_empty_query_raises_value_error(self, populated_retriever):
        with pytest.raises(ValueError, match="Query string cannot be empty"):
            populated_retriever.search("")
        with pytest.raises(ValueError, match="Query string cannot be empty"):
            populated_retriever.search("   \n\t")

    def test_invalid_top_k_raises_value_error(self, populated_retriever):
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            populated_retriever.search("exam schedule", top_k=0)
        with pytest.raises(ValueError, match="top_k must be a positive integer"):
            populated_retriever.search("exam schedule", top_k=-1)

    def test_empty_index_returns_empty_list(self):
        store = SQLiteVectorStore(db_path=":memory:")
        model = FastHashEmbeddingModel(dimension=64)
        retriever = VectorRetriever(embedding_model=model, vector_store=store)
        results = retriever.search("mid semester exams", top_k=5)
        assert results == []

    def test_successful_retrieval_and_result_fields(self, populated_retriever):
        results = populated_retriever.search("When are mid examinations for VII semester?", top_k=2)
        assert len(results) > 0
        top = results[0]
        assert top.chunk_id == "chk_exam"
        assert -1.0 <= top.cosine_similarity <= 1.0
        assert 0.0 <= top.normalized_score <= 1.0
        assert top.score == top.normalized_score
        assert top.metadata["department"] == "CSE"
        assert top.provenance["source_path"] == "exam.pdf"

    def test_retrieval_with_metadata_filter(self, populated_retriever):
        results = populated_retriever.search(
            "rules and regulations", top_k=5, filters={"regulation": "R23"}
        )
        assert len(results) == 1
        assert results[0].chunk_id == "chk_att"

    def test_incompatible_model_raises_error(self):
        store = SQLiteVectorStore(db_path=":memory:")
        # Store has a manifest for 768-d model
        store.save_manifest(
            IndexManifest(
                embedding_provider="ollama",
                embedding_model="nomic-embed-text",
                embedding_dimension=768,
                total_vectors=10,
            )
        )
        # But retriever is configured with 64-d FastHash
        model = FastHashEmbeddingModel(dimension=64)
        retriever = VectorRetriever(embedding_model=model, vector_store=store)

        with pytest.raises(IndexCompatibilityError, match="Dimension mismatch"):
            retriever.search("query text")
