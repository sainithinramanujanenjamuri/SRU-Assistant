"""Preliminary comparative retrieval benchmark for Phase 5 (Dense vs BM25 vs Hybrid).

Evaluates Dense Semantic, BM25 Lexical, Hybrid RRF, and Hybrid Weighted retrieval
across the five academic query types specified in roadmap.md:
1. Semantic Concept Queries
2. Course Code Queries
3. Date Queries
4. Regulation Queries
5. Exact Term Queries

Reuses the Phase 3 synthetic evaluation corpus to ensure controlled, reproducible comparisons.
"""
from __future__ import annotations



import time
from typing import Any

from retrieval.embeddings.benchmark import SYNTHETIC_EVALUATION_CORPUS
from retrieval.embeddings.fast_hash import FastHashEmbeddingModel
from retrieval.fusion.hybrid import HybridRetriever
from retrieval.lexical.bm25 import BM25Index, BM25Retriever
from retrieval.models import VectorRecord
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore

# Benchmark queries categorized according to roadmap.md Phase 5 specification
BENCHMARK_QUERIES = [
    {
        "category": "Semantic Concept Query",
        "query": "Which tree structures and graph algorithms are taught?",
        "relevant_chunk_ids": ["eval_chunk_syllabus_trees"],
    },
    {
        "category": "Course Code Query",
        "query": "23CSE302T course syllabus",
        "relevant_chunk_ids": ["eval_chunk_syllabus_trees"],
    },
    {
        "category": "Date Query",
        "query": "12 September 2026 examination schedule",
        "relevant_chunk_ids": ["eval_chunk_mid_exam"],
    },
    {
        "category": "Regulation Query",
        "query": "Regulation R23 attendance rules",
        "relevant_chunk_ids": ["eval_chunk_attendance"],
    },
    {
        "category": "Exact Term Query",
        "query": "Dussehra vacation academic calendar",
        "relevant_chunk_ids": ["eval_chunk_calendar_holidays"],
    },
]


def setup_benchmark_environment():
    """Build in-memory SQLite vector store and BM25 index for benchmark evaluation."""
    embedding_model = FastHashEmbeddingModel(dimension=384)
    vector_store = SQLiteVectorStore(db_path=":memory:")

    # Index into vector store
    records = []
    for item in SYNTHETIC_EVALUATION_CORPUS:
        vec = embedding_model.embed_text(item["text"])
        records.append(
            VectorRecord(
                chunk_id=item["chunk_id"],
                document_id="doc_" + item["chunk_id"],
                text=item["text"],
                chunk_content_hash="hash_" + item["chunk_id"],
                vector=vec,
                metadata=item["metadata"],
            )
        )
    vector_store.add_records(records)
    dense_retriever = VectorRetriever(embedding_model=embedding_model, vector_store=vector_store)

    # Index into BM25
    bm25_index = BM25Index()
    for item in SYNTHETIC_EVALUATION_CORPUS:
        bm25_index.add_or_update_chunk(
            chunk_id=item["chunk_id"],
            document_id="doc_" + item["chunk_id"],
            text=item["text"],
            chunk_content_hash="hash_" + item["chunk_id"],
            metadata=item["metadata"],
        )
    lexical_retriever = BM25Retriever(bm25_index)

    return dense_retriever, lexical_retriever


def evaluate_retriever_method(
    retriever_name: str,
    search_fn,
    queries: list[dict[str, Any]],
    top_k: int = 5,
) -> dict[str, Any]:
    """Evaluate a retrieval configuration over benchmark queries."""
    r1_hits = 0
    r3_hits = 0
    reciprocal_ranks: list[float] = []
    latencies_ms: list[float] = []
    per_query_results = []

    for q in queries:
        query_text = q["query"]
        relevant_ids = set(q["relevant_chunk_ids"])

        t0 = time.perf_counter()
        results = search_fn(query_text, top_k)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        latencies_ms.append(elapsed_ms)

        retrieved_ids = [r.chunk_id for r in results]

        # Recall@1
        if retrieved_ids and retrieved_ids[0] in relevant_ids:
            r1_hits += 1

        # Recall@3
        if any(cid in relevant_ids for cid in retrieved_ids[:3]):
            r3_hits += 1

        # Reciprocal Rank
        rr = 0.0
        for rank, cid in enumerate(retrieved_ids, start=1):
            if cid in relevant_ids:
                rr = 1.0 / rank
                break
        reciprocal_ranks.append(rr)

        per_query_results.append({
            "category": q["category"],
            "query": query_text,
            "top_1": retrieved_ids[0] if retrieved_ids else None,
            "is_hit": bool(retrieved_ids and retrieved_ids[0] in relevant_ids),
            "rank": int(1.0 / rr) if rr > 0 else None,
            "latency_ms": round(elapsed_ms, 2),
        })

    total = len(queries)
    return {
        "method": retriever_name,
        "total_queries": total,
        "recall_at_1": round(r1_hits / total, 4),
        "recall_at_3": round(r3_hits / total, 4),
        "mrr": round(sum(reciprocal_ranks) / total, 4),
        "mean_latency_ms": round(sum(latencies_ms) / total, 2),
        "per_query_results": per_query_results,
    }


def run_hybrid_retrieval_benchmark() -> dict[str, Any]:
    """Execute the preliminary Phase 5 comparative retrieval benchmark."""
    dense_retriever, lexical_retriever = setup_benchmark_environment()

    hybrid_rrf = HybridRetriever(
        dense_retriever=dense_retriever,
        lexical_retriever=lexical_retriever,
        fusion_method="rrf",
        dense_candidate_k=10,
        lexical_candidate_k=10,
        rrf_k=60,
    )

    hybrid_weighted = HybridRetriever(
        dense_retriever=dense_retriever,
        lexical_retriever=lexical_retriever,
        fusion_method="weighted",
        dense_candidate_k=10,
        lexical_candidate_k=10,
        dense_weight=0.5,
    )

    print("=" * 75)
    print("SRU ASSISTANT — PRELIMINARY PHASE 5 RETRIEVAL COMPARISON")
    print("Synthetic SR University Evaluation Set (5 Query Categories)")
    print("=" * 75)

    configs = [
        ("Dense Only (FastHash)", lambda q, k: dense_retriever.search(q, top_k=k)),
        ("BM25 Only", lambda q, k: lexical_retriever.search(q, top_k=k)),
        ("Hybrid (RRF k=60)", lambda q, k: hybrid_rrf.search(q, top_k=k)),
        ("Hybrid (Weighted alpha=0.5)", lambda q, k: hybrid_weighted.search(q, top_k=k)),
    ]

    all_results = {}
    for name, fn in configs:
        res = evaluate_retriever_method(name, fn, BENCHMARK_QUERIES, top_k=5)
        all_results[name] = res

    # Print comparative results table
    print(f"{'Method':<26} | {'Recall@1':<10} | {'Recall@3':<10} | {'MRR':<10} | {'Mean Latency':<12}")
    print("-" * 75)
    for name, metrics in all_results.items():
        print(
            f"{name:<26} | "
            f"{metrics['recall_at_1']:<10.4f} | "
            f"{metrics['recall_at_3']:<10.4f} | "
            f"{metrics['mrr']:<10.4f} | "
            f"{metrics['mean_latency_ms']:<7.2f} ms"
        )
    print("=" * 75)

    # Detailed query breakdown
    print("\nPER-QUERY BREAKDOWN:")
    for i, q in enumerate(BENCHMARK_QUERIES, start=1):
        print(f"\n[{i}] Category: {q['category']}")
        print(f"    Query   : \"{q['query']}\"")
        for name in all_results:
            q_res = all_results[name]["per_query_results"][i - 1]
            status = "HIT" if q_res["is_hit"] else f"MISS (Rank: {q_res['rank']})"
            print(f"    {name:<26}: {status:<15} ({q_res['latency_ms']:.2f} ms)")
    print("=" * 75)

    return all_results


if __name__ == "__main__":
    run_hybrid_retrieval_benchmark()
