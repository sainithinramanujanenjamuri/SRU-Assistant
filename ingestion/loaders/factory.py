"""Document loader factory and registry."""

from pathlib import Path

from ingestion.loaders.base import BaseDocumentLoader, UnsupportedDocumentError
from ingestion.loaders.docx_loader import DOCXLoader
from ingestion.loaders.pdf_loader import PDFLoader
from ingestion.loaders.txt_loader import TXTLoader


class DocumentLoaderFactory:
    """Registry and factory for resolving format-specific document loaders."""

    def __init__(self) -> None:
        self._loaders: list[BaseDocumentLoader] = [
            PDFLoader(),
            DOCXLoader(),
            TXTLoader(),
        ]

    def register_loader(self, loader: BaseDocumentLoader) -> None:
        """Register a new document loader."""
        self._loaders.insert(0, loader)

    def get_loader(self, path: Path) -> BaseDocumentLoader:
        """Find the matching loader for a given file path.

        Raises UnsupportedDocumentError if no loader supports the extension.
        """
        for loader in self._loaders:
            if loader.can_load(path):
                return loader

        raise UnsupportedDocumentError(
            f"No supported loader found for file extension '{path.suffix}': {path.name}",
            file_path=path,
        )


_default_factory = DocumentLoaderFactory()


def get_loader_for_file(path: Path) -> BaseDocumentLoader:
    """Convenience helper to get the appropriate loader for a file."""
    return _default_factory.get_loader(path)
