"""End-to-end integration tests for BaselineRAGPipeline with HybridRetriever."""

from pathlib import Path

import pytest

from generation.llm.deterministic import DeterministicAnswerGenerator
from generation.pipeline import BaselineRAGPipeline
from generation.prompts.context_builder import ContextBuilder
from ingestion.chunking.models import Chunk, ChunkMetadata, ChunkProvenance
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.fusion.hybrid import HybridRetriever
from retrieval.lexical.bm25 import BM25Index, BM25Retriever
from retrieval.vectorstore.indexer import VectorIndexer
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


@pytest.fixture
def integrated_chunks() -> list[Chunk]:
    return [
        Chunk(
            chunk_id="chk_syllabus_001",
            document_id="doc_syllabus_23cse302t",
            chunk_index=0,
            text="Course 23CSE302T Data Structures: Covers binary trees, graph algorithms, and asymptotic complexity.",
            token_count=15,
            char_count=100,
            word_count=13,
            metadata=ChunkMetadata(
                document_id="doc_syllabus_23cse302t",
                document_name="syllabus_23cse302t.pdf",
                document_type=".pdf",
                department="Computer Science and Engineering",
                semester="III",
                academic_year="2026-27",
            ),
            provenance=ChunkProvenance(
                document_id="doc_syllabus_23cse302t",
                source_file="syllabus_23cse302t.pdf",
                page_numbers=[1],
            ),
        ),
        Chunk(
            chunk_id="chk_calendar_001",
            document_id="doc_calendar_2026_27",
            chunk_index=0,
            text="Academic Calendar 2026-27: Mid-Semester Examination I is held from 12 September 2026 to 16 September 2026.",
            token_count=18,
            char_count=108,
            word_count=16,
            metadata=ChunkMetadata(
                document_id="doc_calendar_2026_27",
                document_name="calendar.txt",
                document_type=".txt",
                department="University Wide",
                semester="All",
                academic_year="2026-27",
            ),
            provenance=ChunkProvenance(
                document_id="doc_calendar_2026_27",
                source_file="calendar.txt",
                page_numbers=[1],
            ),
        ),
    ]


@pytest.fixture
def hybrid_rag_pipeline(integrated_chunks: list[Chunk], tmp_path: Path) -> BaselineRAGPipeline:
    # 1. Setup dense vector store and indexer
    db_path = tmp_path / "test_vector.db"
    vector_store = SQLiteVectorStore(db_path=db_path)
    embedding_model = FastHashEmbeddingModel(dimension=64)
    vector_indexer = VectorIndexer(embedding_model=embedding_model, vector_store=vector_store)
    vector_indexer.index_chunks(integrated_chunks)
    dense_retriever = VectorRetriever(embedding_model=embedding_model, vector_store=vector_store)

    # 2. Setup BM25 index
    bm25_index = BM25Index()
    for chk in integrated_chunks:
        bm25_index.add_or_update_chunk(
            chunk_id=chk.chunk_id,
            document_id=chk.document_id,
            text=chk.text,
            chunk_content_hash="hash_" + chk.chunk_id,
            metadata=chk.metadata.model_dump(),
            provenance=chk.provenance.model_dump(),
        )
    lexical_retriever = BM25Retriever(bm25_index)

    # 3. Setup HybridRetriever
    hybrid_retriever = HybridRetriever(
        dense_retriever=dense_retriever,
        lexical_retriever=lexical_retriever,
        fusion_method="rrf",
        dense_candidate_k=5,
        lexical_candidate_k=5,
    )

    # 4. Setup RAG pipeline with deterministic generator
    generator = DeterministicAnswerGenerator()
    context_builder = ContextBuilder(relevance_threshold=0.30)
    return BaselineRAGPipeline(
        retriever=hybrid_retriever,
        generator=generator,
        context_builder=context_builder,
    )


def test_hybrid_rag_course_code_query(hybrid_rag_pipeline: BaselineRAGPipeline):
    """End-to-end question answering on exact course code 23CSE302T."""
    response = hybrid_rag_pipeline.answer_query(
        query="What topics are covered in 23CSE302T?",
        top_k=3,
    )

    assert response.is_grounded is True
    assert "23CSE302T" in response.answer or "binary trees" in response.answer.lower()
    assert len(response.evidence) > 0
    top_ev = response.evidence[0]
    assert top_ev.chunk_id == "chk_syllabus_001"
    assert response.retrieval_mode == "hybrid"
    assert response.hybrid_meta is not None
    assert response.hybrid_meta["dense_candidates_retrieved"] >= 1
    assert response.hybrid_meta["lexical_candidates_retrieved"] >= 1


def test_hybrid_rag_calendar_query(hybrid_rag_pipeline: BaselineRAGPipeline):
    """End-to-end question answering on academic calendar schedule."""
    response = hybrid_rag_pipeline.answer_query(
        query="When are the mid examinations scheduled?",
        top_k=3,
    )

    assert response.is_grounded is True
    assert "12 September 2026" in response.answer or "16 September 2026" in response.answer
    assert any(ev.chunk_id == "chk_calendar_001" for ev in response.evidence)


def test_hybrid_rag_out_of_domain_query(hybrid_rag_pipeline: BaselineRAGPipeline):
    """Out of domain query triggers institutional fallback."""
    response = hybrid_rag_pipeline.answer_query(
        query="What are the timings for the university swimming pool?",
        top_k=3,
    )

    assert response.is_grounded is False
    assert "couldn't find sufficient information" in response.answer
