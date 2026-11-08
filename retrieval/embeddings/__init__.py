"""Embedding model interfaces and vector generation components."""

from retrieval.embeddings.base import BaseEmbeddingModel
from retrieval.embeddings.benchmark import (
    run_embedding_latency_benchmark,
    run_preliminary_retrieval_benchmark,
)
from retrieval.embeddings.factory import get_embedding_model
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.embeddings.ollama import OllamaEmbeddingModel
from retrieval.embeddings.sentence_transformers import SentenceTransformersEmbeddingModel

__all__ = [
    "BaseEmbeddingModel",
    "FastHashEmbeddingModel",
    "OllamaEmbeddingModel",
    "SentenceTransformersEmbeddingModel",
    "get_embedding_model",
    "run_embedding_latency_benchmark",
    "run_preliminary_retrieval_benchmark",
]
