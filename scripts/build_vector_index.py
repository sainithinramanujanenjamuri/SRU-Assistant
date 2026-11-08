from __future__ import annotations


"""CLI script to build or update the persistent vector database from chunk dataset files."""

import argparse
import sys
import time
from pathlib import Path

# Ensure project root is on sys.path for direct CLI execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import get_settings
from retrieval.embeddings.factory import get_embedding_model
from retrieval.vectorstore.indexer import VectorIndexer
from retrieval.vectorstore.sqlite_store import SQLiteVectorStore


def main() -> None:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Index structured document chunks into the persistent SRU Assistant vector database."
    )
    parser.add_argument(
        "--chunks-dir",
        type=str,
        default=settings.chunks_dir,
        help=f"Directory containing chunk JSON datasets (default: {settings.chunks_dir})",
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
        help=f"Embedding provider: fasthash, ollama, sentence_transformers (default: {settings.embedding_provider})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=settings.embedding_model,
        help=f"Embedding model identifier (default: {settings.embedding_model})",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=settings.embedding_batch_size,
        help=f"Batch size for embedding operations (default: {settings.embedding_batch_size})",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing vector store records before indexing",
    )
    args = parser.parse_args()

    chunks_dir = Path(args.chunks_dir)
    print("=" * 70)
    print("SRU ASSISTANT — VECTOR DATABASE INDEXER (PHASE 3)")
    print("=" * 70)
    print(f"Chunks directory : {chunks_dir}")
    print(f"Vector DB path   : {args.db_path}")
    print(f"Provider         : {args.provider}")
    print(f"Model            : {args.model}")
    print(f"Batch size       : {args.batch_size}")
    print("-" * 70)

    # Initialize components
    try:
        model = get_embedding_model(provider=args.provider, model_name=args.model)
    except Exception as e:
        print(f"Error initializing embedding model: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        store = SQLiteVectorStore(db_path=args.db_path)
    except Exception as e:
        print(f"Error initializing vector database: {e}", file=sys.stderr)
        sys.exit(1)

    if args.clear:
        print("Clearing existing vector store records as requested...")
        store.clear()

    indexer = VectorIndexer(embedding_model=model, vector_store=store)

    if not chunks_dir.exists():
        print(f"Chunks directory does not exist: {chunks_dir}. Creating empty directory.")
        chunks_dir.mkdir(parents=True, exist_ok=True)

    json_files = sorted(chunks_dir.glob("*.json"))
    print(f"Found {len(json_files)} chunk dataset file(s).")

    total_requested = 0
    total_indexed = 0
    total_updated = 0
    total_skipped = 0
    total_failed = 0
    t0 = time.perf_counter()

    for path in json_files:
        try:
            report = indexer.index_dataset_file(path, batch_size=args.batch_size)
            print(
                f"  [{path.name}] "
                f"Requested: {report.chunks_requested} | "
                f"New: {report.chunks_indexed} | "
                f"Updated: {report.chunks_updated} | "
                f"Skipped: {report.chunks_skipped} | "
                f"Failed: {report.chunks_failed} "
                f"({report.elapsed_seconds:.2f}s)"
            )
            total_requested += report.chunks_requested
            total_indexed += report.chunks_indexed
            total_updated += report.chunks_updated
            total_skipped += report.chunks_skipped
            total_failed += report.chunks_failed
        except Exception as e:
            print(f"  [ERROR] Failed to index {path.name}: {e}", file=sys.stderr)

    total_time = time.perf_counter() - t0
    final_count = store.count()
    manifest = store.get_manifest()

    print("-" * 70)
    print("INDEXING SUMMARY:")
    print(f"  Total chunks processed : {total_requested}")
    print(f"  New vectors inserted   : {total_indexed}")
    print(f"  Stale vectors updated  : {total_updated}")
    print(f"  Unchanged skipped      : {total_skipped}")
    print(f"  Failed embeddings      : {total_failed}")
    print(f"  Final total in DB      : {final_count}")
    print(f"  Total elapsed time     : {total_time:.2f}s")
    if manifest:
        print(f"  Index Manifest         : {manifest.embedding_provider}/{manifest.embedding_model} "
              f"({manifest.embedding_dimension}-d, metric={manifest.distance_metric})")
    print("=" * 70)


if __name__ == "__main__":
    main()
