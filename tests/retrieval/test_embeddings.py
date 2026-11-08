"""Unit tests for embedding subsystem (FastHash, Ollama, SentenceTransformers, Factory)."""

import math

import numpy as np
import pytest

from retrieval.embeddings.base import BaseEmbeddingModel
from retrieval.embeddings.factory import get_embedding_model
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.embeddings.ollama import OllamaEmbeddingModel
from retrieval.embeddings.sentence_transformers import SentenceTransformersEmbeddingModel
from retrieval.models import EmbeddingError


class TestBaseEmbeddingModel:
    """Test BaseEmbeddingModel abstract class helpers and validation."""

    def test_normalize_vector_unit_length(self):
        vec = [3.0, 4.0, 0.0]
        normalized = BaseEmbeddingModel.normalize_vector(vec)
        assert len(normalized) == 3
        norm = math.sqrt(sum(x * x for x in normalized))
        assert pytest.approx(norm, abs=1e-6) == 1.0
        assert pytest.approx(normalized[0], abs=1e-6) == 0.6
        assert pytest.approx(normalized[1], abs=1e-6) == 0.8

    def test_normalize_zero_vector(self):
        vec = [0.0, 0.0, 0.0]
        normalized = BaseEmbeddingModel.normalize_vector(vec)
        assert normalized == [0.0, 0.0, 0.0]

    def test_validate_text_rejects_empty(self):
        with pytest.raises(ValueError, match="Cannot embed empty"):
            BaseEmbeddingModel.validate_text("")
        with pytest.raises(ValueError, match="Cannot embed empty"):
            BaseEmbeddingModel.validate_text("   \n\t  ")

    def test_validate_text_rejects_non_string(self):
        with pytest.raises(ValueError, match="Expected string input"):
            BaseEmbeddingModel.validate_text(None)  # type: ignore
        with pytest.raises(ValueError, match="Expected string input"):
            BaseEmbeddingModel.validate_text(123)  # type: ignore


class TestFastHashEmbeddingModel:
    """Test FastHash deterministic lexical-feature embedding baseline."""

    def test_initialization(self):
        model = FastHashEmbeddingModel(dimension=384, model_name="fasthash-test")
        assert model.dimension == 384
        assert model.model_name == "fasthash-test"
        assert model.provider_name == "fasthash"

    def test_invalid_dimension_raises(self):
        with pytest.raises(ValueError, match="Dimension must be positive"):
            FastHashEmbeddingModel(dimension=0)
        with pytest.raises(ValueError, match="Dimension must be positive"):
            FastHashEmbeddingModel(dimension=-5)

    def test_determinism_identical_input(self):
        model = FastHashEmbeddingModel(dimension=384)
        text = "SR University B.Tech VII Semester Examination Schedule"
        vec1 = model.embed_text(text)
        vec2 = model.embed_text(text)
        assert vec1 == vec2

    def test_l2_normalization_unit_length(self):
        model = FastHashEmbeddingModel(dimension=384)
        text = "Regulation R23 requires 75% attendance across all courses."
        vec = model.embed_text(text)
        norm = np.linalg.norm(np.array(vec, dtype=np.float32))
        assert pytest.approx(float(norm), abs=1e-5) == 1.0

    def test_batch_matches_single(self):
        model = FastHashEmbeddingModel(dimension=384)
        texts = [
            "Mid-Semester Examination-I timetable",
            "Advanced Data Structures 23CSE302T Unit II Trees",
            "Department of Computer Science and Engineering",
        ]
        batch_vecs = model.embed_batch(texts)
        single_vecs = [model.embed_text(t) for t in texts]
        assert len(batch_vecs) == len(single_vecs)
        for bv, sv in zip(batch_vecs, single_vecs):
            assert bv == sv

    def test_empty_batch_returns_empty_list(self):
        model = FastHashEmbeddingModel(dimension=384)
        assert model.embed_batch([]) == []

    def test_deterministic_lexical_feature_behavior(self):
        """Shared academic terminology yields higher cosine similarity than disjoint text."""
        model = FastHashEmbeddingModel(dimension=384)
        target = "Mid-Semester Examination-I schedule for B.Tech students"
        related = "Schedule of Mid-Semester Examination-I announced by University"
        disjoint = "Organic chemistry reaction kinetics and hydrocarbon synthesis"

        v_target = np.array(model.embed_text(target), dtype=np.float32)
        v_related = np.array(model.embed_text(related), dtype=np.float32)
        v_disjoint = np.array(model.embed_text(disjoint), dtype=np.float32)

        sim_related = float(np.dot(v_target, v_related))
        sim_disjoint = float(np.dot(v_target, v_disjoint))

        assert sim_related > sim_disjoint
        assert sim_related > 0.4  # Significant lexical overlap


class TestOllamaEmbeddingModel:
    """Test Ollama embedding model adapter."""

    def test_initialization(self):
        model = OllamaEmbeddingModel(
            model_name="nomic-embed-text",
            base_url="http://localhost:11434",
            dimension=768,
        )
        assert model.provider_name == "ollama"
        assert model.model_name == "nomic-embed-text"
        assert model.dimension == 768

    def test_empty_query_rejected_locally(self):
        model = OllamaEmbeddingModel()
        with pytest.raises(ValueError):
            model.embed_text("   ")

    def test_status_check_returns_tuple(self):
        model = OllamaEmbeddingModel(base_url="http://127.0.0.1:9999")  # Unused port
        available, msg = model.is_available()
        assert available is False
        assert "Cannot connect" in msg or "Error" in msg

    def test_connection_error_raises_expected_exception(self):
        # Point to unreachable port to verify clear error message without hang
        model = OllamaEmbeddingModel(base_url="http://127.0.0.1:9999", timeout_seconds=1.0)
        with pytest.raises(EmbeddingError):
            model.embed_text("test query")


class TestSentenceTransformersEmbeddingModel:
    """Test SentenceTransformers embedding model adapter."""

    def test_is_available_tuple(self):
        available, msg = SentenceTransformersEmbeddingModel.is_available()
        assert isinstance(available, bool)
        assert isinstance(msg, str)

    def test_rejection_of_empty_text(self):
        model = SentenceTransformersEmbeddingModel()
        with pytest.raises(ValueError):
            model.embed_text("")


class TestEmbeddingFactory:
    """Test get_embedding_model factory."""

    def test_default_fasthash_factory(self):
        model = get_embedding_model(provider="fasthash", dimension=256)
        assert isinstance(model, FastHashEmbeddingModel)
        assert model.dimension == 256

    def test_ollama_factory(self):
        model = get_embedding_model(provider="ollama", model_name="nomic-embed-text")
        assert isinstance(model, OllamaEmbeddingModel)
        assert model.model_name == "nomic-embed-text"

    def test_sentence_transformers_factory(self):
        model = get_embedding_model(provider="sentence_transformers", model_name="all-MiniLM-L6-v2")
        assert isinstance(model, SentenceTransformersEmbeddingModel)

    def test_unsupported_provider_raises_value_error(self):
        with pytest.raises(ValueError, match="Unsupported embedding provider"):
            get_embedding_model(provider="unknown_provider")
