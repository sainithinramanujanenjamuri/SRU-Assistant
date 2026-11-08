"""CLI script to build or update the persistent BM25 inverted index from chunk dataset files."""

import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path for direct CLI execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import get_settings
from ingestion.chunking.models import Chunk, ChunkDataset
from retrieval.lexical.indexer import BM25Indexer


def main() -> None:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Index structured document chunks into the persistent SRU Assistant BM25 inverted index."
    )
    parser.add_argument(
        "--chunks-dir",
        type=str,
        default=settings.chunks_dir,
        help=f"Directory containing chunk JSON datasets (default: {settings.chunks_dir})",
    )
    parser.add_argument(
        "--index-path",
        type=str,
        default=str(settings.bm25_index_path),
        help=f"Path to output BM25 index JSON file (default: {settings.bm25_index_path})",
    )
    parser.add_argument(
        "--k1",
        type=float,
        default=settings.bm25_k1,
        help=f"BM25 term saturation parameter k1 (default: {settings.bm25_k1})",
    )
    parser.add_argument(
        "--b",
        type=float,
        default=settings.bm25_b,
        help=f"BM25 document length normalization parameter b (default: {settings.bm25_b})",
    )
    parser.add_argument(
        "--force-rebuild",
        action="store_true",
        help="Completely rebuild index from scratch, clearing existing inverted index",
    )
    args = parser.parse_args()

    chunks_dir = Path(args.chunks_dir)
    print("=" * 70)
    print("SRU ASSISTANT — BM25 LEXICAL INDEXER (PHASE 5)")
    print("=" * 70)
    print(f"Chunks directory : {chunks_dir}")
    print(f"BM25 index path  : {args.index_path}")
    print(f"Parameters       : k1={args.k1}, b={args.b}")
    print(f"Force rebuild    : {args.force_rebuild}")
    print("-" * 70)

    if not chunks_dir.exists():
        print(f"Error: Chunks directory does not exist: {chunks_dir}", file=sys.stderr)
        sys.exit(1)

    chunk_files = sorted(list(chunks_dir.glob("*.json")))
    if not chunk_files:
        print(f"No chunk JSON files found in {chunks_dir}", file=sys.stderr)
        sys.exit(0)

    all_chunks: list[Chunk] = []
    print(f"Discovered {len(chunk_files)} chunk dataset file(s):")
    for f in chunk_files:
        try:
            dataset = ChunkDataset.model_validate_json(f.read_text(encoding="utf-8"))
            print(f"  - {f.name}: {len(dataset.chunks)} chunk(s)")
            all_chunks.extend(dataset.chunks)
        except Exception as e:
            print(f"  - Warning: Failed to parse {f.name}: {e}", file=sys.stderr)

    if not all_chunks:
        print("No valid chunks loaded for indexing.", file=sys.stderr)
        sys.exit(1)

    indexer = BM25Indexer(index_path=args.index_path)
    report = indexer.index_chunks(all_chunks, force_rebuild=args.force_rebuild)

    print("-" * 70)
    print("BM25 INDEXING REPORT:")
    print(f"  Total chunks submitted : {report.chunks_requested}")
    print(f"  New chunks indexed     : {report.chunks_indexed}")
    print(f"  Chunks updated         : {report.chunks_updated}")
    print(f"  Chunks skipped         : {report.chunks_skipped} (idempotent)")
    print(f"  Chunks removed         : {report.chunks_removed}")
    print(f"  Duration               : {report.elapsed_seconds:.4f} s")
    if report.manifest:
        print("INDEX MANIFEST:")
        print(f"  Index Version          : {report.manifest.index_version}")
        print(f"  Tokenizer Version      : {report.manifest.tokenizer_version}")
        print(f"  Total Chunks in Index  : {report.manifest.total_chunks}")
        print(f"  Vocabulary Size        : {report.manifest.vocabulary_size} terms")
        print(f"  Average Document Length: {report.manifest.average_document_length:.2f} tokens")
    print("=" * 70)
    print("BM25 indexing completed successfully.")


if __name__ == "__main__":
    main()
