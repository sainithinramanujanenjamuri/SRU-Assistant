"""Base interface for modular academic structure detectors."""

from abc import ABC, abstractmethod
from typing import Any

from ingestion.models import DocumentElement


class BaseStructureDetector(ABC):
    """Abstract base class for all individual academic structure detection modules."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the structure detector."""

    @abstractmethod
    def detect(self, elements: list[DocumentElement], full_text: str) -> list[Any]:
        """Detect relevant academic structures from document elements and full text."""
