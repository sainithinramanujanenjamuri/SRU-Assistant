"""Chunking data models, provenance tracking, and dataset container for Phase 2."""
from __future__ import annotations



import json
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from pathlib import Path
from typing import Any


from pydantic import BaseModel, Field


class ChunkProvenance(BaseModel):
    """Provenance tracing the originating source location(s) for an academic chunk."""

    document_id: str = Field(description="SHA-256 hash of originating source file")
    source_file: str = Field(description="Original source filename")
    page_numbers: list[int] = Field(default_factory=list, description="Sorted contributing page numbers")
    line_numbers: list[int] = Field(default_factory=list, description="Sorted contributing line numbers")
    element_ids: list[str] = Field(default_factory=list, description="IDs of source DocumentElements in this chunk")


class ChunkMetadata(BaseModel):
    """Metadata attached to a chunk, maintaining clear distinction between inherited and chunk-local facts."""

    # Inherited document-level metadata
    document_id: str = Field(description="Source document SHA-256 identity")
    document_name: str = Field(description="Source document filename")
    document_type: str = Field(description="Source file format (.pdf, .docx, .txt)")
    department: str | None = Field(default=None, description="Document-level academic department")
    program: str | None = Field(default=None, description="Document-level academic program (B.Tech, M.Tech)")
    academic_year: str | None = Field(default=None, description="Document-level academic year (e.g. 2026-27)")
    semester: str | None = Field(default=None, description="Document-level semester (e.g. Semester VII)")
    category: str | None = Field(default=None, description="Document category (e.g. syllabus, academic_calendar)")
    regulations: list[str] = Field(default_factory=list, description="Document-level regulations")

    # Structural hierarchy context
    section_path: str = Field(default="", description="Hierarchical heading path (e.g. Syllabus > Unit II > Trees)")
    heading_hierarchy: list[str] = Field(default_factory=list, description="Ancestral heading titles stack")

    # Chunk-local detected entities (evidence present directly within chunk text)
    chunk_course_codes: list[str] = Field(default_factory=list, description="Course codes explicitly inside this chunk")
    chunk_dates: list[str] = Field(default_factory=list, description="Calendar dates explicitly inside this chunk")
    chunk_regulations: list[str] = Field(default_factory=list, description="Regulations explicitly inside this chunk")
    chunk_examinations: list[str] = Field(default_factory=list, description="Exams explicitly inside this chunk")


class Chunk(BaseModel):
    """An atomic, retrieval-ready unit of academic knowledge with complete provenance."""

    chunk_id: str = Field(description="Deterministic chunk identifier: {document_id}_chunk_{index:04d}")
    document_id: str = Field(description="Source document canonical SHA-256 identity")
    chunk_index: int = Field(description="0-indexed sequential order within document")
    text: str = Field(description="Chunk content ready for embedding and retrieval")
    token_count: int = Field(description="Canonical size metric in tokens")
    char_count: int = Field(description="Diagnostic character count")
    word_count: int = Field(description="Diagnostic word count")
    is_table: bool = Field(default=False, description="Flag indicating whether chunk represents table content")
    is_oversized: bool = Field(default=False, description="Flag indicating if chunk intentionally exceeds max_tokens")
    metadata: ChunkMetadata = Field(description="Contextual and entity metadata")
    provenance: ChunkProvenance = Field(description="Complete source location provenance")
    table_metadata: dict[str, Any] | None = Field(default=None, description="Table-specific splitting/grid metadata")


class DuplicateChunkReport(BaseModel):
    """Report on duplicate chunks detected within a single document."""

    chunk_ids: list[str] = Field(description="Chunk IDs sharing identical text")
    text_snippet: str = Field(description="Truncated snippet of duplicate text")
    occurrences: int = Field(description="Number of times this exact text appears")


class ChunkDataset(BaseModel):
    """Dataset container holding all chunks generated for an academic document."""

    document_id: str = Field(description="Source document canonical SHA-256 identity")
    chunks: list[Chunk] = Field(default_factory=list, description="Sequential list of retrieval-ready chunks")
    total_chunks: int = Field(default=0, description="Total number of chunks")
    avg_token_count: float = Field(default=0.0, description="Average tokens per chunk")
    min_token_count: int = Field(default=0, description="Minimum chunk token count")
    max_token_count: int = Field(default=0, description="Maximum chunk token count")
    table_chunks_count: int = Field(default=0, description="Number of table chunks")
    duplicate_reports: list[DuplicateChunkReport] = Field(default_factory=list, description="In-document duplicates")
    generated_timestamp: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())

    def validate_dataset(self) -> list[str]:
        """Perform validation checks on chunks and dataset integrity.

        Returns a list of validation error descriptions (empty if 100% valid).
        """
        errors: list[str] = []
        if self.total_chunks != len(self.chunks):
            errors.append(f"total_chunks ({self.total_chunks}) does not match len(chunks) ({len(self.chunks)})")

        seen_ids: set[str] = set()
        for idx, chunk in enumerate(self.chunks):
            if not chunk.text.strip():
                errors.append(f"Chunk at index {idx} has empty text")
            if chunk.chunk_index != idx:
                errors.append(f"Chunk at index {idx} has mismatched chunk_index ({chunk.chunk_index})")
            if chunk.document_id != self.document_id:
                errors.append(f"Chunk {chunk.chunk_id} document_id does not match dataset document_id")
            if chunk.chunk_id in seen_ids:
                errors.append(f"Duplicate chunk_id found: {chunk.chunk_id}")
            seen_ids.add(chunk.chunk_id)
            if not chunk.provenance.element_ids:
                errors.append(f"Chunk {chunk.chunk_id} has empty element_ids provenance")

        return errors

    def to_dict(self) -> dict[str, Any]:
        """Serialize dataset to dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Serialize dataset to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_to_file(self, output_path: Path) -> Path:
        """Save dataset to a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_json(), encoding="utf-8")
        return output_path

    @classmethod
    def load_from_file(cls, input_path: Path) -> "ChunkDataset":
        """Load dataset from a JSON file."""
        data = json.loads(input_path.read_text(encoding="utf-8"))
        return cls.model_validate(data)
