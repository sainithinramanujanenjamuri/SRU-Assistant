from __future__ import annotations


"""Interactive and argument-driven CLI to query the semantic vector index."""

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct CLI execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import get_settings
from retrieval.embeddings.factory import get_embedding_model
from retrieval.vectorstore.retriever import VectorRetriever
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


def main() -> None:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Search for relevant academic chunks using semantic vector similarity."
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Natural language query string (if omitted, prompts interactively)",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=settings.retrieval_top_k,
        help=f"Number of chunks to retrieve (default: {settings.retrieval_top_k})",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=settings.vectorstore_path,
        help=f"Path to SQLite vector database (default: {settings.vectorstore_path})",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=settings.embedding_provider,
        help=f"Embedding provider (default: {settings.embedding_provider})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=settings.embedding_model,
        help=f"Embedding model (default: {settings.embedding_model})",
    )
    # Metadata filters
    parser.add_argument("--department", type=str, default=None, help="Filter by department (e.g. CSE)")
    parser.add_argument("--semester", type=str, default=None, help="Filter by semester (e.g. VII)")
    parser.add_argument("--regulation", type=str, default=None, help="Filter by regulation (e.g. R23)")
    parser.add_argument("--academic-year", type=str, default=None, help="Filter by academic year (e.g. 2026-27)")
    parser.add_argument("--document-type", type=str, default=None, help="Filter by document type")

    args = parser.parse_args()

    # Get query
    query = args.query
    if not query:
        print("=" * 70)
        print("SRU ASSISTANT — SEMANTIC SEARCH (PHASE 3)")
        print("=" * 70)
        try:
            query = input("Enter your academic query: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    if not query:
        print("Empty query provided. Exiting.")
        sys.exit(1)

    # Initialize components
    try:
        model = get_embedding_model(provider=args.provider, model_name=args.model)
        store = SQLiteVectorStore(db_path=args.db_path)
        retriever = VectorRetriever(embedding_model=model, vector_store=store)
    except Exception as e:
        print(f"Error initializing retriever: {e}", file=sys.stderr)
        sys.exit(1)

    # Build filters
    filters = {}
    if args.department:
        filters["department"] = args.department
    if args.semester:
        filters["semester"] = args.semester
    if args.regulation:
        filters["regulation"] = args.regulation
    if args.academic_year:
        filters["academic_year"] = args.academic_year
    if args.document_type:
        filters["document_type"] = args.document_type

    print(f"\nQuery: '{query}'")
    if filters:
        print(f"Active Filters: {filters}")
    print(f"Retrieving top {args.top_k} results from {args.db_path}...\n")

    try:
        results = retriever.search(query=query, top_k=args.top_k, filters=filters or None)
    except Exception as e:
        print(f"Retrieval failed: {e}", file=sys.stderr)
        sys.exit(1)

    if not results:
        print("No matching chunks found in the vector store.")
        sys.exit(0)

    print(f"Found {len(results)} matching chunk(s):\n")
    print("-" * 70)
    for rank, res in enumerate(results, start=1):
        sec_path = res.provenance.get("section_path") or "N/A"
        page_start = res.provenance.get("page_start")
        page_end = res.provenance.get("page_end")
        page_info = f"p. {page_start}" if page_start == page_end else f"pp. {page_start}-{page_end}"
        doc_id_short = res.document_id[:12] if len(res.document_id) > 12 else res.document_id

        print(f"#{rank} | Chunk: {res.chunk_id} | Doc: {doc_id_short}... | {page_info}")
        print(f"   Cosine Sim: {res.cosine_similarity:+.4f} | Normalized Score: {res.normalized_score:.4f}")
        print(f"   Section: {sec_path}")
        snippet = res.text.replace("\n", " ")
        if len(snippet) > 200:
            snippet = snippet[:197] + "..."
        print(f"   Text: {snippet}")
        print("-" * 70)


if __name__ == "__main__":
    main()
