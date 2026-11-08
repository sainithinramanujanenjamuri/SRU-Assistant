from __future__ import annotations


"""CLI script for side-by-side hybrid retrieval inspection and comparison."""

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct CLI execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import get_settings
from retrieval.embeddings.factory import get_embedding_model
from retrieval.fusion.hybrid import HybridRetriever
from retrieval.lexical.bm25 import BM25Retriever
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


def main() -> None:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Inspect and compare Dense, BM25, and Hybrid retrieval for SRU Assistant."
    )
    parser.add_argument("--query", type=str, help="Search query string")
    parser.add_argument("--top-k", type=int, default=5, help="Number of results to return (default: 5)")
    parser.add_argument(
        "--mode",
        type=str,
        default="hybrid",
        choices=["hybrid", "dense", "lexical"],
        help="Retrieval mode to test (default: hybrid)",
    )
    parser.add_argument(
        "--fusion-method",
        type=str,
        default="rrf",
        choices=["rrf", "weighted"],
        help="Fusion algorithm: rrf or weighted (default: rrf)",
    )
    parser.add_argument(
        "--department",
        type=str,
        default=None,
        help="Metadata filter: department",
    )
    parser.add_argument(
        "--regulation",
        type=str,
        default=None,
        help="Metadata filter: regulation (e.g. R23)",
    )
    args = parser.parse_args()

    # Initialize components
    print("=" * 70)
    print("SRU ASSISTANT — HYBRID RETRIEVAL INSPECTOR (PHASE 5)")
    print("=" * 70)
    print(f"Mode          : {args.mode}")
    print(f"Fusion Method : {args.fusion_method}")
    print(f"Top-K         : {args.top_k}")

    # Build filters
    filters = {}
    if args.department:
        filters["department"] = args.department
    if args.regulation:
        filters["regulation"] = args.regulation
    if filters:
        print(f"Active Filters: {filters}")
    print("-" * 70)

    try:
        embedding_model = get_embedding_model(
            provider=settings.embedding_provider,
            model_name=settings.embedding_model,
        )
        vector_store = SQLiteVectorStore(db_path=settings.vectorstore_path)
        dense_retriever = VectorRetriever(embedding_model=embedding_model, vector_store=vector_store)
        lexical_retriever = BM25Retriever.from_file(index_path=settings.bm25_index_path)

        hybrid_retriever = HybridRetriever(
            dense_retriever=dense_retriever,
            lexical_retriever=lexical_retriever,
            fusion_method=args.fusion_method,
            dense_candidate_k=settings.hybrid_dense_candidate_k,
            lexical_candidate_k=settings.hybrid_lexical_candidate_k,
            rrf_k=settings.hybrid_rrf_k,
            dense_weight=settings.hybrid_dense_weight,
            lexical_weight=settings.hybrid_lexical_weight,
            allow_channel_fallback=settings.hybrid_allow_fallback,
        )
    except Exception as e:
        print(f"Initialization error: {e}", file=sys.stderr)
        sys.exit(1)

    def execute_query(query_text: str) -> None:
        if not query_text.strip():
            return
        print(f"\nQUERY: \"{query_text.strip()}\"")
        print("-" * 70)
        try:
            results = hybrid_retriever.search(
                query=query_text.strip(),
                top_k=args.top_k,
                filters=filters if filters else None,
                mode=args.mode,
            )
        except Exception as e:
            print(f"Search failed: {e}", file=sys.stderr)
            return

        if not results:
            print("No matching candidates found.")
            return

        print(f"Found {len(results)} candidate(s):")
        for i, res in enumerate(results, start=1):
            d_rank = f"#{res.dense_rank}" if res.dense_rank else "N/A"
            d_score = f"{res.dense_score:.4f}" if res.dense_score is not None else "N/A"
            l_rank = f"#{res.lexical_rank}" if res.lexical_rank else "N/A"
            l_score = f"{res.lexical_score:.4f}" if res.lexical_score is not None else "N/A"

            meta = res.metadata or {}
            doc_name = meta.get("document_name") or res.document_id

            print(f"\n  [{i}] Chunk ID: {res.chunk_id} | Document: {doc_name}")
            print(f"      Fused Score: {res.fused_score:.6f} (Normalized: {res.normalized_fused_score:.4f})")
            print(f"      Dense Rank : {d_rank} (Score: {d_score}) | Lexical Rank: {l_rank} (Score: {l_score})")
            text_snippet = res.text.strip().replace("\n", " ")
            if len(text_snippet) > 120:
                text_snippet = text_snippet[:117] + "..."
            print(f"      Text: \"{text_snippet}\"")

        meta = hybrid_retriever.last_meta
        if meta:
            print("\nOBSERVABILITY METRICS:")
            print(f"  Execution Mode      : {meta.actual_mode} (Requested: {meta.requested_mode})")
            print(f"  Candidates Retrieved: Dense={meta.dense_candidates_retrieved}, Lexical={meta.lexical_candidates_retrieved}")
            print(f"  Dense Latency       : {meta.dense_latency_ms:.2f} ms")
            print(f"  Lexical Latency     : {meta.lexical_latency_ms:.2f} ms")
            print(f"  Fusion Latency      : {meta.fusion_latency_ms:.2f} ms")
            print(f"  Total Retrieval Time: {meta.total_retrieval_latency_ms:.2f} ms")
        print("=" * 70)

    if args.query:
        execute_query(args.query)
    else:
        print("Entering interactive hybrid query session. Type 'exit' or 'quit' to stop.\n")
        while True:
            try:
                user_input = input("sru-hybrid> ").strip()
                if user_input.lower() in ("exit", "quit", "q"):
                    break
                execute_query(user_input)
            except (KeyboardInterrupt, EOFError):
                break


if __name__ == "__main__":
    main()
