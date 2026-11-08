"""Base abstractions and exceptions for document loaders."""
from __future__ import annotations


import hashlib
from abc import ABC, abstractmethod
from pathlib import Path

from ingestion.models import ExtractedDocument


class DocumentLoadingError(Exception):
    """Base exception for all document loading failures."""


    def __init__(self, message: str, file_path: Path | None = None) -> None:
        super().__init__(message)
        self.file_path = file_path


class UnsupportedDocumentError(DocumentLoadingError):
    """Raised when encountering a file type not supported by the loader."""


class CorruptedDocumentError(DocumentLoadingError):
    """Raised when a document cannot be parsed due to corruption or malformed structure."""


class EmptyDocumentError(DocumentLoadingError):
    """Raised when a document contains zero bytes or zero readable content."""


def compute_file_sha256(path: Path) -> str:
    """Compute the deterministic SHA-256 hex digest of the complete file content.

    Ensures that identical file contents produce identical IDs regardless of filename.
    """
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class BaseDocumentLoader(ABC):
    """Abstract base class for all file-format specific document loaders."""

    @property
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        """List of lowercase file extensions supported by this loader (e.g. ['.pdf'])."""

    def can_load(self, path: Path) -> bool:
        """Check if this loader supports the specified file."""
        return path.suffix.lower() in self.supported_extensions

    def validate_file(self, path: Path) -> None:
        """Verify file existence and non-zero size before loading."""
        if not path.exists():
            raise DocumentLoadingError(f"File does not exist: {path}", file_path=path)
        if not path.is_file():
            raise DocumentLoadingError(f"Path is not a regular file: {path}", file_path=path)
        if path.stat().st_size == 0:
            raise EmptyDocumentError(f"Document is empty (zero bytes): {path.name}", file_path=path)

    @abstractmethod
    def load(self, path: Path) -> ExtractedDocument:
        """Extract content from file and return an ExtractedDocument preserving raw content.

        Must retain source provenance (page or line numbers) where available.
        """
