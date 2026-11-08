"""End-to-end Document Ingestion Pipeline for SRU Assistant (Phase 1).

Transforms raw academic documents into clean, structured, metadata-rich
intermediate representations while preserving raw extraction and unbroken provenance.
"""
from __future__ import annotations



import logging
from dataclasses import dataclass, field
from pathlib import Path

from app.config import get_settings
from ingestion.loaders import DocumentLoaderFactory
from ingestion.loaders.base import DocumentLoadingError
from ingestion.metadata import MetadataExtractor
from ingestion.models import ProcessedDocument
from ingestion.processors import DocumentCleaner, StructureDetector

logger = logging.getLogger(__name__)


@dataclass
class DocumentProcessingError:
    """Record of a failure during document processing."""

    file_path: str
    error_type: str
    message: str


@dataclass
class IngestionBatchResult:
    """Summary of a directory-level ingestion batch execution."""

    total_files_found: int = 0
    successful_count: int = 0
    failed_count: int = 0
    processed_documents: list[ProcessedDocument] = field(default_factory=list)
    failures: list[DocumentProcessingError] = field(default_factory=list)


class DocumentPipeline:
    """Orchestrates document loading, cleaning, structure detection, and metadata extraction."""

    def __init__(
        self,
        loader_factory: DocumentLoaderFactory | None = None,
        cleaner: DocumentCleaner | None = None,
        structure_detector: StructureDetector | None = None,
        metadata_extractor: MetadataExtractor | None = None,
        header_footer_threshold: float = 0.8,
    ) -> None:
        self.loader_factory = loader_factory or DocumentLoaderFactory()
        self.cleaner = cleaner or DocumentCleaner(header_footer_threshold=header_footer_threshold)
        self.structure_detector = structure_detector or StructureDetector()
        self.metadata_extractor = metadata_extractor or MetadataExtractor()

    def process_file(self, file_path: Path) -> ProcessedDocument:
        """Process a single academic document into its intermediate structured representation.

        Preserves raw extraction, applies conservative cleaning, detects academic entities,
        and assigns evidence-based metadata with complete provenance.
        """
        path = Path(file_path).resolve()
        loader = self.loader_factory.get_loader(path)

        # 1. Raw Extraction
        extracted_doc = loader.load(path)

        # 2. Cleaning & Normalization (produces separate cleaned representation)
        cleaned_elements = self.cleaner.clean(extracted_doc)

        # 3. Cleaned Full Text
        cleaned_text = "\n\n".join(e.content for e in cleaned_elements)

        # 4. Modular Structure Detection
        structures = self.structure_detector.detect_structures(cleaned_elements, cleaned_text)

        # 5. Evidence-based Metadata Extraction
        metadata = self.metadata_extractor.extract_metadata(extracted_doc, structures)

        # 6. Assemble Final Intermediate Representation
        processed_doc = ProcessedDocument(
            document_id=extracted_doc.document_id,
            metadata=metadata,
            elements=cleaned_elements,
            raw_elements_count=len(extracted_doc.elements),
            raw_text=extracted_doc.raw_text,
            cleaned_text=cleaned_text,
            academic_structures=structures,
        )

        return processed_doc

    def process_directory(
        self,
        input_dir: Path,
        output_dir: Path,
        supported_extensions: list[str] | None = None,
    ) -> IngestionBatchResult:
        """Process all supported documents in a directory with failure isolation.

        A single corrupted or invalid document will not crash the batch.
        """
        settings = get_settings()
        extensions = supported_extensions or settings.ingestion_supported_extensions

        input_path = Path(input_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        batch_result = IngestionBatchResult()

        if not input_path.exists() or not input_path.is_dir():
            logger.warning("Input directory does not exist or is not a directory: %s", input_path)
            return batch_result

        # Scan for matching files
        all_candidate_files: list[Path] = []
        for ext in extensions:
            all_candidate_files.extend(input_path.glob(f"*{ext}"))
            all_candidate_files.extend(input_path.glob(f"*{ext.upper()}"))

        # Deduplicate and filter out hidden/system files
        target_files = sorted(list({p for p in all_candidate_files if p.is_file() and not p.name.startswith(".")}))
        batch_result.total_files_found = len(target_files)

        for file_path in target_files:
            try:
                processed_doc = self.process_file(file_path)
                # Save intermediate representation to output directory
                output_file = output_path / f"{processed_doc.document_id}.json"
                processed_doc.save_to_file(output_file)

                batch_result.successful_count += 1
                batch_result.processed_documents.append(processed_doc)
                logger.info("Successfully processed: %s -> %s", file_path.name, output_file.name)
            except DocumentLoadingError as e:
                batch_result.failed_count += 1
                batch_result.failures.append(
                    DocumentProcessingError(
                        file_path=str(file_path),
                        error_type=e.__class__.__name__,
                        message=str(e),
                    )
                )
                logger.error("Document loading error for %s: %s", file_path.name, e)
            except Exception as e:
                batch_result.failed_count += 1
                batch_result.failures.append(
                    DocumentProcessingError(
                        file_path=str(file_path),
                        error_type=e.__class__.__name__,
                        message=str(e),
                    )
                )
                logger.error("Unexpected error processing %s: %s", file_path.name, e)

        return batch_result
