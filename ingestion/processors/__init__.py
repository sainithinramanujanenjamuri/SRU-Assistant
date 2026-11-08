"""Document processors package (cleaners, text normalizers, academic structure detectors)."""

from ingestion.processors.cleaner import DocumentCleaner
from ingestion.processors.structure_detector import StructureDetector

__all__ = [
    "DocumentCleaner",
    "StructureDetector",
]
