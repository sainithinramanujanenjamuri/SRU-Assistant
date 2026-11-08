"""SRU Assistant - Document ingestion package."""

from ingestion.loaders import (
    BaseDocumentLoader,
    CorruptedDocumentError,
    DocumentLoaderFactory,
    DocumentLoadingError,
    DOCXLoader,
    EmptyDocumentError,
    PDFLoader,
    TXTLoader,
    UnsupportedDocumentError,
    compute_file_sha256,
    get_loader_for_file,
)
from ingestion.metadata import MetadataExtractor
from ingestion.models import (
    DetectedAcademicStructures,
    DocumentElement,
    DocumentMetadata,
    ElementProvenance,
    ElementType,
    ExtractedDocument,
    ProcessedDocument,
    TableData,
)
from ingestion.pipeline import DocumentPipeline, DocumentProcessingError, IngestionBatchResult
from ingestion.processors import DocumentCleaner, StructureDetector

__all__ = [
    "BaseDocumentLoader",
    "CorruptedDocumentError",
    "DOCXLoader",
    "DetectedAcademicStructures",
    "DocumentCleaner",
    "DocumentElement",
    "DocumentLoaderFactory",
    "DocumentLoadingError",
    "DocumentMetadata",
    "DocumentPipeline",
    "DocumentProcessingError",
    "ElementProvenance",
    "ElementType",
    "EmptyDocumentError",
    "ExtractedDocument",
    "IngestionBatchResult",
    "MetadataExtractor",
    "PDFLoader",
    "ProcessedDocument",
    "StructureDetector",
    "TXTLoader",
    "TableData",
    "UnsupportedDocumentError",
    "compute_file_sha256",
    "get_loader_for_file",
]
