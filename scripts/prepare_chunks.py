"""Knowledge Preparation CLI script for SRU Assistant (Phase 2).

Transforms processed documents in 'documents/processed/' into retrieval-ready
chunk datasets stored in 'documents/chunks/'.
"""
from __future__ import annotations



import sys
from pathlib import Path

# Ensure project root is on sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from ingestion.chunking.pipeline import ChunkingPipeline


def prepare_chunks(
    processed_dir: Path | None = None,
    chunks_dir: Path | None = None,
) -> int:
    """Run chunking pipeline on all processed intermediate documents."""
    settings = get_settings()
    input_path = processed_dir or Path(settings.processed_documents_dir)
    output_path = chunks_dir or Path(settings.chunks_dir)

    print("=" * 70)
    print("SRU ASSISTANT -- PHASE 2 KNOWLEDGE PREPARATION & CHUNKING")
    print("=" * 70)
    print(f"Processed Docs Directory : {input_path.resolve()}")
    print(f"Chunks Output Directory  : {output_path.resolve()}")
    print(f"Target Chunk Tokens      : {settings.chunk_target_tokens}")
    print(f"Overlap Tokens           : {settings.chunk_overlap_tokens}")
    print(f"Min / Max Tokens         : {settings.chunk_min_tokens} / {settings.chunk_max_tokens}")
    print("-" * 70)

    all_files = list(input_path.glob("*.json"))
    print(f"Candidate JSON Files Found: {len(all_files)}")

    if not all_files:
        print("Knowledge preparation: NO PROCESSED DOCUMENTS FOUND.")
        print("Reason: No intermediate JSON files found in documents/processed/.")
        print("Note: Run document ingestion or test pipelines first.")
        print("=" * 70)
        return 0

    pipeline = ChunkingPipeline()
    batch_result = pipeline.chunk_directory(input_path, output_path)

    print(f"Documents Processed      : {batch_result.successful_count} / {batch_result.total_files_found}")
    print(f"Total Chunks Generated   : {batch_result.total_chunks_generated}")
    print(f"Table Chunks Preserved   : {batch_result.total_table_chunks}")
    print(f"In-Document Duplicates   : {batch_result.total_duplicates_detected}")
    print(f"Failures Encountered     : {batch_result.failed_count}")

    if batch_result.datasets:
        all_tokens = [c.token_count for ds in batch_result.datasets for c in ds.chunks]
        if all_tokens:
            overall_avg = sum(all_tokens) / len(all_tokens)
            overall_min = min(all_tokens)
            overall_max = max(all_tokens)
            print(f"Token Distribution       : Avg={overall_avg:.1f} | Min={overall_min} | Max={overall_max}")

    for ds in batch_result.datasets:
        print(f"  [OK] Doc ID: {ds.document_id[:16]}... -> {ds.total_chunks} chunks (Avg: {ds.avg_token_count} tok)")

    for fail in batch_result.failures:
        print(f"  [FAIL] {Path(fail['file_path']).name}: [{fail['error_type']}] {fail['message']}")

    print("=" * 70)
    return 0 if batch_result.failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(prepare_chunks())
