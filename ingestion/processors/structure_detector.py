"""Composite academic structure detector aggregating all modular detectors."""

from ingestion.models import (
    DetectedAcademicStructures,
    DocumentElement,
    ElementType,
)
from ingestion.processors.detectors import (
    AcademicYearDetector,
    CourseCodeDetector,
    DateDetector,
    DepartmentDetector,
    DocumentCategoryDetector,
    ExaminationDetector,
    RegulationDetector,
    SemesterDetector,
)


class StructureDetector:
    """Composite detector orchestrating modular academic entity and structure detectors."""

    def __init__(self) -> None:
        self.course_code_detector = CourseCodeDetector()
        self.regulation_detector = RegulationDetector()
        self.department_detector = DepartmentDetector()
        self.semester_detector = SemesterDetector()
        self.academic_year_detector = AcademicYearDetector()
        self.examination_detector = ExaminationDetector()
        self.date_detector = DateDetector()
        self.category_detector = DocumentCategoryDetector()

    def detect_structures(
        self, elements: list[DocumentElement], full_text: str
    ) -> DetectedAcademicStructures:
        """Run all modular detectors and extract academic structures."""
        headings: list[dict[str, any]] = []
        for elem in elements:
            if elem.element_type in (ElementType.TITLE, ElementType.HEADING):
                headings.append({
                    "element_id": elem.element_id,
                    "title": elem.content,
                    "page_number": elem.provenance.page_number,
                    "line_number": elem.provenance.line_number,
                    "structural_index": elem.provenance.structural_index,
                })

        return DetectedAcademicStructures(
            course_codes=self.course_code_detector.detect(elements, full_text),
            regulations=self.regulation_detector.detect(elements, full_text),
            departments=self.department_detector.detect(elements, full_text),
            semesters=self.semester_detector.detect(elements, full_text),
            academic_years=self.academic_year_detector.detect(elements, full_text),
            examinations=self.examination_detector.detect(elements, full_text),
            dates=self.date_detector.detect(elements, full_text),
            categories=self.category_detector.detect(elements, full_text),
            headings=headings,
        )
