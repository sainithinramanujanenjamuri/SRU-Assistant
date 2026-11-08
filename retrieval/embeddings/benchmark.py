"""Benchmarking utility for embedding models and preliminary retrieval evaluation."""

import time
from collections.abc import Sequence
from typing import Any

import numpy as np

from retrieval.embeddings.base import BaseEmbeddingModel

# ==============================================================================
# Preliminary Evaluation Dataset (Synthetic SR University Academic Queries)
# ==============================================================================

SYNTHETIC_EVALUATION_CORPUS = [
    {
        "chunk_id": "eval_chunk_mid_exam",
        "text": (
            "SR University Examination Branch: Mid-Semester Examination-I for B.Tech VII Semester "
            "commences from 12 September 2026 to 16 September 2026. Detailed timetable is posted."
        ),
        "metadata": {"department": "CSE", "semester": "VII", "document_type": "examination_schedule"},
    },
    {
        "chunk_id": "eval_chunk_attendance",
        "text": (
            "Regulation R23 Academic Regulations: Minimum 75% attendance is mandatory in aggregate across "
            "all theory and practical courses to be eligible for end semester university examinations. "
            "Condonation up to 10% allowed on valid medical grounds."
        ),
        "metadata": {"regulation": "R23", "document_type": "academic_regulations"},
    },
    {
        "chunk_id": "eval_chunk_syllabus_trees",
        "text": (
            "Course 23CSE302T Advanced Data Structures: Unit II Trees and Graphs. Binary Search Trees, "
            "AVL Trees, Red-Black Trees, B-Trees, graph traversals BFS and DFS, Dijkstra shortest path algorithm."
        ),
        "metadata": {"course_code": "23CSE302T", "semester": "V", "document_type": "syllabus"},
    },
    {
        "chunk_id": "eval_chunk_calendar_holidays",
        "text": (
            "Academic Calendar 2026-27: Dussehra vacation from 05 October 2026 to 10 October 2026. "
            "Classes resume on 12 October 2026 for all undergraduate engineering programs."
        ),
        "metadata": {"academic_year": "2026-27", "document_type": "academic_calendar"},
    },
]

SYNTHETIC_EVALUATION_QUERIES = [
    {
        "query": "When are the mid examinations scheduled for VII semester?",
        "relevant_chunk_ids": ["eval_chunk_mid_exam"],
    },
    {
        "query": "What is the minimum attendance requirement under Regulation R23?",
        "relevant_chunk_ids": ["eval_chunk_attendance"],
    },
    {
        "query": "Which tree structures are covered in Advanced Data Structures course 23CSE302T?",
        "relevant_chunk_ids": ["eval_chunk_syllabus_trees"],
    },
    {
        "query": "When is the Dussehra vacation according to the academic calendar?",
        "relevant_chunk_ids": ["eval_chunk_calendar_holidays"],
    },
]


def run_embedding_latency_benchmark(
    model: BaseEmbeddingModel,
    sample_texts: Sequence[str],
    warmup_runs: int = 1,
) -> dict[str, Any]:
    """Measure single and batch latency, throughput, dimension, and normalization consistency."""
    if not sample_texts:
        raise ValueError("sample_texts cannot be empty")

    # Warmup run
    for _ in range(warmup_runs):
        _ = model.embed_text(sample_texts[0])

    # Single-item latency benchmark
    t0 = time.perf_counter()
    single_vectors: list[list[float]] = []
    for text in sample_texts:
        single_vectors.append(model.embed_text(text))
    single_elapsed = time.perf_counter() - t0

    # Batch latency benchmark
    t1 = time.perf_counter()
    _ = model.embed_batch(sample_texts)
    batch_elapsed = time.perf_counter() - t1

    # Measure normalization error: abs(||v||_2 - 1.0)
    norm_errors = [abs(float(np.linalg.norm(v)) - 1.0) for v in single_vectors]
    max_norm_error = max(norm_errors) if norm_errors else 0.0

    return {
        "provider": model.provider_name,
        "model_name": model.model_name,
        "dimension": model.dimension,
        "sample_count": len(sample_texts),
        "single_total_seconds": round(single_elapsed, 4),
        "single_avg_latency_ms": round((single_elapsed / len(sample_texts)) * 1000.0, 2),
        "single_throughput_chunks_sec": round(len(sample_texts) / max(single_elapsed, 1e-6), 2),
        "batch_total_seconds": round(batch_elapsed, 4),
        "batch_avg_latency_ms": round((batch_elapsed / len(sample_texts)) * 1000.0, 2),
        "batch_throughput_chunks_sec": round(len(sample_texts) / max(batch_elapsed, 1e-6), 2),
        "max_l2_norm_error": max_norm_error,
    }


def run_preliminary_retrieval_benchmark(
    model: BaseEmbeddingModel,
    k_values: Sequence[int] = (1, 3, 5),
) -> dict[str, Any]:
    """Run a preliminary evaluation on the synthetic academic evaluation set.

    Computes Recall@K and MRR (Mean Reciprocal Rank).
    """
    corpus_texts = [item["text"] for item in SYNTHETIC_EVALUATION_CORPUS]
    corpus_ids = [item["chunk_id"] for item in SYNTHETIC_EVALUATION_CORPUS]

    # Pre-embed corpus
    corpus_vectors = np.array(model.embed_batch(corpus_texts), dtype=np.float32)

    recalls_at_k: dict[int, list[float]] = {k: [] for k in k_values}
    reciprocal_ranks: list[float] = []

    for q_item in SYNTHETIC_EVALUATION_QUERIES:
        query_text = q_item["query"]
        relevant_ids = set(q_item["relevant_chunk_ids"])

        q_vec = np.array(model.embed_text(query_text), dtype=np.float32)
        scores = np.dot(corpus_vectors, q_vec)

        # Ranked indices descending by score, tie-break by corpus_id ascending
        sorted_indices = sorted(
            range(len(scores)),
            key=lambda idx: (-scores[idx], corpus_ids[idx]),
        )
        ranked_chunk_ids = [corpus_ids[idx] for idx in sorted_indices]

        # Calculate Reciprocal Rank
        rr = 0.0
        for rank_1_indexed, cid in enumerate(ranked_chunk_ids, start=1):
            if cid in relevant_ids:
                rr = 1.0 / rank_1_indexed
                break
        reciprocal_ranks.append(rr)

        # Calculate Recall@K
        for k in k_values:
            top_k_ids = set(ranked_chunk_ids[:k])
            hits = len(relevant_ids.intersection(top_k_ids))
            recall = hits / len(relevant_ids) if relevant_ids else 0.0
            recalls_at_k[k].append(recall)

    mrr = sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0.0
    mean_recalls = {f"Recall@{k}": round(sum(v) / len(v), 4) for k, v in recalls_at_k.items()}

    return {
        "provider": model.provider_name,
        "model_name": model.model_name,
        "queries_evaluated": len(SYNTHETIC_EVALUATION_QUERIES),
        "corpus_size": len(SYNTHETIC_EVALUATION_CORPUS),
        "mrr": round(mrr, 4),
        **mean_recalls,
    }
