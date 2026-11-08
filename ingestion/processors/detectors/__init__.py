"""Modular academic structure detectors package."""

from ingestion.processors.detectors.academic_year import AcademicYearDetector
from ingestion.processors.detectors.base import BaseStructureDetector
from ingestion.processors.detectors.category import DocumentCategoryDetector
from ingestion.processors.detectors.course_code import CourseCodeDetector
from ingestion.processors.detectors.date_detector import DateDetector
from ingestion.processors.detectors.department import DepartmentDetector
from ingestion.processors.detectors.examination import ExaminationDetector
from ingestion.processors.detectors.regulation import RegulationDetector
from ingestion.processors.detectors.semester import SemesterDetector

__all__ = [
    "AcademicYearDetector",
    "BaseStructureDetector",
    "CourseCodeDetector",
    "DateDetector",
    "DepartmentDetector",
    "DocumentCategoryDetector",
    "ExaminationDetector",
    "RegulationDetector",
    "SemesterDetector",
]
