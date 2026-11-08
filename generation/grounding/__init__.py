"""Grounding validation, entity extraction, and conflict detection subsystem."""

from generation.grounding.conflict_detector import ConflictDetector
from generation.grounding.entities import AcademicEntity, AcademicEntityExtractor
from generation.grounding.validator import GroundingValidator

__all__ = [
    "AcademicEntity",
    "AcademicEntityExtractor",
    "ConflictDetector",
    "GroundingValidator",
]
