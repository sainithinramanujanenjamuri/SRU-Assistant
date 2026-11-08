"""Data models for SRU Assistant Document Intelligence (Phase 1).

Defines intermediate representations, element provenance, academic structures,
and metadata schemas ensuring unbroken provenance, raw extraction preservation,
and strict non-fabrication.
"""
from __future__ import annotations



import json
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    class StrEnum(str, Enum):
        pass

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field



class ElementType(StrEnum):
    """Types of semantic elements extracted from academic documents."""

    TITLE = "title"
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    TABLE = "table"
    LIST_ITEM = "list_item"
    NOTICE_HEADER = "notice_header"
    UNKNOWN = "unknown"


class ElementProvenance(BaseModel):
    """Origin and location trace for a single document element."""

    document_id: str = Field(description="SHA-256 hash of complete source file content")
    source_file: str = Field(description="Original filename or path")
    page_number: int | None = Field(default=None, description="1-indexed page number if applicable")
    line_number: int | None = Field(default=None, description="1-indexed line number if applicable")
    structural_index: int = Field(default=0, description="Sequential element index within document")


class TableData(BaseModel):
    """Structured grid representation of an extracted table."""

    headers: list[str] = Field(default_factory=list, description="Column header strings")
    rows: list[list[str]] = Field(default_factory=list, description="Row grid of string cell contents")
    num_rows: int = Field(default=0, description="Total number of rows including header")
    num_cols: int = Field(default=0, description="Total number of columns")
    markdown: str = Field(default="", description="Rendered markdown representation of the table")


class DocumentElement(BaseModel):
    """A single atomic structured element extracted from a document."""

    element_id: str = Field(description="Deterministic element identifier")
    element_type: ElementType = Field(default=ElementType.PARAGRAPH, description="Type of document element")
    content: str = Field(description="Textual content or markdown representation")
    provenance: ElementProvenance = Field(description="Provenance tracing back to source location")
    table_data: TableData | None = Field(default=None, description="Preserved structured grid if element is a table")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional element-level metadata")


class ExtractedDocument(BaseModel):
    """Unaltered extraction directly from document loaders before cleaning or normalization.

    Preserves the pristine raw text and original elements for full auditing and traceability.
    """

    document_id: str = Field(description="SHA-256 hash of complete source file content")
    file_path: str = Field(description="Source file path on disk")
    file_name: str = Field(description="Source file name")
    file_type: str = Field(description="Normalized file extension (e.g. .pdf, .docx, .txt)")
    file_size_bytes: int = Field(description="Size in bytes of raw file")
    raw_text: str = Field(description="Complete unaltered raw text extracted from file")
    elements: list[DocumentElement] = Field(default_factory=list, description="Initial raw element stream")
    loader_name: str = Field(description="Identifier of loader used")
    extraction_metadata: dict[str, Any] = Field(default_factory=dict, description="Loader-specific extraction metadata")


class DocumentMetadata(BaseModel):
    """Comprehensive, evidence-based metadata schema for academic documents.

    All academic fields must be backed by explicit evidence; otherwise they remain None.
    """

    document_id: str = Field(description="Deterministic SHA-256 identity of complete source file")
    document_name: str = Field(description="Human-readable filename")
    source_path: str = Field(description="Path to original file")
    document_type: str = Field(description="Document format (.pdf, .docx, .txt)")
    file_size_bytes: int = Field(description="Size of source file in bytes")
    department: str | None = Field(default=None, description="Academic department if explicitly detected")
    program: str | None = Field(default=None, description="Academic program (e.g. B.Tech, M.Tech) if detected")
    academic_year: str | None = Field(default=None, description="Academic year (e.g. 2026-27) if detected")
    semester: str | None = Field(default=None, description="Semester (e.g. Semester VII) if detected")
    regulations: list[str] = Field(default_factory=list, description="Detected regulations (e.g. R23, R20)")
    category: str | None = Field(default=None, description="Document category (e.g. syllabus, academic_calendar)")
    version: str | None = Field(default=None, description="Version string if detected")
    ingestion_timestamp: str = Field(description="ISO 8601 ingestion timestamp")


class DetectedAcademicStructures(BaseModel):
    """Academic concepts detected by modular structure detectors."""

    course_codes: list[str] = Field(default_factory=list, description="Detected course codes (e.g. 23CSE302T)")
    regulations: list[str] = Field(default_factory=list, description="Detected regulation identifiers (e.g. R23)")
    departments: list[str] = Field(default_factory=list, description="Detected academic departments")
    semesters: list[str] = Field(default_factory=list, description="Detected academic semesters")
    academic_years: list[str] = Field(default_factory=list, description="Detected academic years")
    examinations: list[str] = Field(default_factory=list, description="Detected examination types / names")
    dates: list[str] = Field(default_factory=list, description="Detected academic calendar dates and ranges")
    categories: list[str] = Field(default_factory=list, description="Detected document categories")
    headings: list[dict[str, Any]] = Field(default_factory=list, description="Extracted headings and section titles")


class ProcessedDocument(BaseModel):
    """Intermediate representation produced by Phase 1 for Phase 2 chunking and retrieval.

    Preserves raw text copy, cleaned elements with unbroken provenance,
    structured tables, and verified academic metadata.
    """

    document_id: str = Field(description="Deterministic SHA-256 identity of complete source file")
    metadata: DocumentMetadata = Field(description="Evidence-based document metadata")
    elements: list[DocumentElement] = Field(description="Cleaned, normalized elements with preserved provenance")
    raw_elements_count: int = Field(description="Number of elements in raw extraction before cleaning")
    raw_text: str = Field(description="Preserved raw extraction text for auditability")
    cleaned_text: str = Field(description="Cleaned, normalized document text")
    academic_structures: DetectedAcademicStructures = Field(description="Detected academic structures")

    def to_dict(self) -> dict[str, Any]:
        """Convert processed document to dictionary."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Convert processed document to formatted JSON string."""
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def save_to_file(self, output_path: Path) -> Path:
        """Save processed document to a JSON file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.to_json(), encoding="utf-8")
        return output_path
