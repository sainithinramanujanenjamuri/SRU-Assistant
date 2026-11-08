"""Validation script for SRU Assistant Document Intelligence (Phase 1).

Processes any documents present in 'documents/raw/' using the Phase 1 pipeline.
If no official SR University documents are found, reports validation as PENDING.
"""
from __future__ import annotations



import sys
from pathlib import Path

# Ensure project root is on sys.path for direct script execution
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings
from ingestion.pipeline import DocumentPipeline


def validate_documents(raw_dir: Path | None = None, processed_dir: Path | None = None) -> int:
    """Run document processing validation on the raw documents directory."""
    settings = get_settings()
    input_path = raw_dir or Path(settings.raw_documents_dir)
    output_path = processed_dir or Path(settings.processed_documents_dir)

    print("=" * 70)
    print("SRU ASSISTANT -- PHASE 1 DOCUMENT INTELLIGENCE VALIDATION")
    print("=" * 70)
    print(f"Raw Documents Directory      : {input_path.resolve()}")
    print(f"Processed Output Directory   : {output_path.resolve()}")

    supported_exts = settings.ingestion_supported_extensions
    all_files = [
        p for p in input_path.glob("*")
        if p.is_file() and p.suffix.lower() in supported_exts and not p.name.startswith(".")
    ]

    print(f"Supported File Formats       : {', '.join(supported_exts)}")
    print(f"Candidate Files Found        : {len(all_files)}")
    print("-" * 70)

    if not all_files:
        print("Official SR University document validation: PENDING")
        print("Reason: No official academic documents (.pdf, .docx, .txt) found in documents/raw/.")
        print("Note: Automated unit and integration tests use deterministic test fixtures.")
        print("=" * 70)
        return 0

    print("Official SR University documents detected! Executing pipeline...")
    pipeline = DocumentPipeline()
    batch_result = pipeline.process_directory(input_path, output_path)

    print(f"Total Files Found: {batch_result.total_files_found}")
    print(f"Successfully Processed: {batch_result.successful_count}")
    print(f"Failures Encountered: {batch_result.failed_count}")

    for doc in batch_result.processed_documents:
        print(f"  [OK] {doc.metadata.document_name} -> ID: {doc.document_id[:16]}...")
        print(f"       Category: {doc.metadata.category} | Dept: {doc.metadata.department} | Sem: {doc.metadata.semester}")
        print(f"       Course Codes: {doc.academic_structures.course_codes} | Regulations: {doc.academic_structures.regulations}")

    for fail in batch_result.failures:
        print(f"  [FAIL] {Path(fail.file_path).name}: [{fail.error_type}] {fail.message}")

    print("=" * 70)
    return 0 if batch_result.failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(validate_documents())
