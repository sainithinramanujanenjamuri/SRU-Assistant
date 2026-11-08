"""SRU Assistant - Retrieval package (embeddings, vector store, lexical search, fusion, filtering, reranking)."""

from retrieval.base import BaseRetriever
from retrieval.embeddings import (
    BaseEmbeddingModel,
    FastHashEmbeddingModel,
    OllamaEmbeddingModel,
    SentenceTransformersEmbeddingModel,
    get_embedding_model,
)
from retrieval.enhanced_retriever import EnhancedRetriever
from retrieval.filtering.metadata_filter import MetadataFilter
from retrieval.fusion.hybrid import HybridRetriever
from retrieval.lexical.bm25 import BM25Index, BM25Retriever
from retrieval.models import (
    EmbeddingError,
    EmbeddingProviderUnavailableError,
    IndexCompatibilityError,
    IndexingReport,
    IndexManifest,
    RetrievalError,
    VectorRecord,
    VectorSearchResult,
    VectorStoreError,
)
from retrieval.query.analyzer import AcademicQueryAnalyzer
from retrieval.reranking import (
    BaseReranker,
    DeterministicCrossEncoderReranker,
    DeterministicCrossFeatureReranker,
    OllamaCrossEncoderReranker,
    PassthroughReranker,
    TransformerCrossEncoderReranker,
    get_reranker,
)
from retrieval.vectorstore import (
    BaseVectorStore,
    SQLiteVectorStore,
    VectorIndexer,
    VectorRetriever,
)

__all__ = [
    "AcademicQueryAnalyzer",
    "BM25Index",
    "BM25Retriever",
    "BaseEmbeddingModel",
    "BaseReranker",
    "BaseRetriever",
    "BaseVectorStore",
    "DeterministicCrossEncoderReranker",
    "DeterministicCrossFeatureReranker",
    "EmbeddingError",
    "EmbeddingProviderUnavailableError",
    "EnhancedRetriever",
    "FastHashEmbeddingModel",
    "HybridRetriever",
    "IndexCompatibilityError",
    "IndexManifest",
    "IndexingReport",
    "MetadataFilter",
    "OllamaCrossEncoderReranker",
    "OllamaEmbeddingModel",
    "PassthroughReranker",
    "RetrievalError",
    "SQLiteVectorStore",
    "SentenceTransformersEmbeddingModel",
    "TransformerCrossEncoderReranker",
    "VectorIndexer",
    "VectorRecord",
    "VectorRetriever",
    "VectorSearchResult",
    "VectorStoreError",
    "get_embedding_model",
    "get_reranker",
]
