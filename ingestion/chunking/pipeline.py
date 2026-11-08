"""Chunking pipeline coordinating document chunking, validation, duplicate detection, and batch execution."""
from __future__ import annotations


import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.config import get_settings
from ingestion.chunking.base import BaseChunker
from ingestion.chunking.models import ChunkDataset
from ingestion.chunking.structure_aware import StructureAwareChunker
from ingestion.models import ProcessedDocument

logger = logging.getLogger(__name__)


class ChunkValidationError(Exception):
    """Raised when generated chunks or datasets fail validation rules."""



@dataclass
class ChunkingBatchResult:
    """Summary of a directory-level chunking batch execution."""

    total_files_found: int = 0
    successful_count: int = 0
    failed_count: int = 0
    total_chunks_generated: int = 0
    total_table_chunks: int = 0
    total_duplicates_detected: int = 0
    datasets: list[ChunkDataset] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)


class ChunkingPipeline:
    """Orchestrates chunk generation, validation, and batch persistence."""

    def __init__(self, chunker: BaseChunker | None = None) -> None:
        settings = get_settings()
        self.chunker = chunker or StructureAwareChunker(
            target_tokens=settings.chunk_target_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
            min_tokens=settings.chunk_min_tokens,
            max_tokens=settings.chunk_max_tokens,
        )

    def chunk_processed_document(self, processed_doc: ProcessedDocument) -> ChunkDataset:
        """Transform a ProcessedDocument into a validated ChunkDataset with in-document duplicate detection."""
        chunks = self.chunker.chunk_document(processed_doc)

        token_counts = [c.token_count for c in chunks] if chunks else [0]
        avg_tokens = sum(token_counts) / len(token_counts) if chunks else 0.0
        min_tokens = min(token_counts) if chunks else 0
        max_tokens = max(token_counts) if chunks else 0
        table_chunks = sum(1 for c in chunks if c.is_table)

        # Detect in-document duplicate chunk texts without deletion
        dup_reports = BaseChunker.detect_in_document_duplicates(chunks)

        dataset = ChunkDataset(
            document_id=processed_doc.document_id,
            chunks=chunks,
            total_chunks=len(chunks),
            avg_token_count=round(avg_tokens, 2),
            min_token_count=min_tokens,
            max_token_count=max_tokens,
            table_chunks_count=table_chunks,
            duplicate_reports=dup_reports,
        )

        validation_errors = dataset.validate_dataset()
        if validation_errors:
            raise ChunkValidationError(
                f"Chunk validation failed for {processed_doc.document_id}: {'; '.join(validation_errors)}"
            )

        return dataset

    def chunk_directory(
        self,
        processed_dir: Path,
        output_dir: Path,
    ) -> ChunkingBatchResult:
        """Process all processed JSON documents in a directory with failure isolation."""
        processed_path = Path(processed_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        batch_result = ChunkingBatchResult()

        if not processed_path.exists() or not processed_path.is_dir():
            logger.warning("Processed directory does not exist: %s", processed_path)
            return batch_result

        target_files = sorted(list(processed_path.glob("*.json")))
        batch_result.total_files_found = len(target_files)

        for file_path in target_files:
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                processed_doc = ProcessedDocument.model_validate(data)

                dataset = self.chunk_processed_document(processed_doc)
                output_file = output_path / f"{processed_doc.document_id}_chunks.json"
                dataset.save_to_file(output_file)

                batch_result.successful_count += 1
                batch_result.total_chunks_generated += dataset.total_chunks
                batch_result.total_table_chunks += dataset.table_chunks_count
                batch_result.total_duplicates_detected += len(dataset.duplicate_reports)
                batch_result.datasets.append(dataset)
                logger.info("Successfully chunked: %s (%d chunks)", file_path.name, dataset.total_chunks)
            except Exception as e:
                batch_result.failed_count += 1
                batch_result.failures.append({
                    "file_path": str(file_path),
                    "error_type": e.__class__.__name__,
                    "message": str(e),
                })
                logger.error("Failed to chunk %s: %s", file_path.name, e)

        return batch_result
