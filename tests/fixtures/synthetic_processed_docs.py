"""Synthetic ProcessedDocument test fixtures generator for Phase 2 Knowledge Preparation.

Provides deterministic synthetic fixtures covering 12 structural edge cases.
NOTE: These fixtures are strictly synthetic test artifacts and not official university archives.
"""
from __future__ import annotations



from ingestion.models import (
    DetectedAcademicStructures,
    DocumentElement,
    DocumentMetadata,
    ElementProvenance,
    ElementType,
    ProcessedDocument,
    TableData,
)


def create_fixture_normal_syllabus(doc_id: str = "doc_syllabus_normal") -> ProcessedDocument:
    """Fixture 1: Normal syllabus section with headings and paragraphs."""
    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.HEADING,
            content="### Course Overview",
            provenance=ElementProvenance(document_id=doc_id, source_file="syllabus.pdf", page_number=1, structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.PARAGRAPH,
            content="This course covers fundamental algorithms and data structures for B.Tech Computer Science under Regulation R23.",
            provenance=ElementProvenance(document_id=doc_id, source_file="syllabus.pdf", page_number=1, structural_index=2),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e3",
            element_type=ElementType.HEADING,
            content="### Learning Objectives",
            provenance=ElementProvenance(document_id=doc_id, source_file="syllabus.pdf", page_number=1, structural_index=3),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e4",
            element_type=ElementType.PARAGRAPH,
            content="Students will learn tree traversals, graph algorithms, and asymptotic complexity analysis for course 23CSE302T.",
            provenance=ElementProvenance(document_id=doc_id, source_file="syllabus.pdf", page_number=1, structural_index=4),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="syllabus.pdf",
        source_path="/test/syllabus.pdf",
        document_type=".pdf",
        file_size_bytes=1024,
        department="Computer Science and Engineering",
        program="B.Tech",
        academic_year="2026-27",
        semester="Semester VII",
        regulations=["R23"],
        category="syllabus",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(
            course_codes=["23CSE302T"],
            regulations=["R23"],
            departments=["Computer Science and Engineering"],
            semesters=["Semester VII"],
            academic_years=["2026-27"],
        ),
    )


def create_fixture_nested_headings(doc_id: str = "doc_nested_headings") -> ProcessedDocument:
    """Fixture 2: Deeply nested heading hierarchy (# Title > ## Dept > ### Subject > #### Unit)."""
    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.TITLE,
            content="# SR University Curriculum",
            provenance=ElementProvenance(document_id=doc_id, source_file="nested.docx", structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.HEADING,
            content="## Department of Computer Science and Engineering",
            provenance=ElementProvenance(document_id=doc_id, source_file="nested.docx", structural_index=2),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e3",
            element_type=ElementType.HEADING,
            content="### Data Structures",
            provenance=ElementProvenance(document_id=doc_id, source_file="nested.docx", structural_index=3),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e4",
            element_type=ElementType.HEADING,
            content="#### Unit II: Trees and Binary Search Trees",
            provenance=ElementProvenance(document_id=doc_id, source_file="nested.docx", structural_index=4),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e5",
            element_type=ElementType.PARAGRAPH,
            content="Detailed study of AVL trees, red-black trees, and heap structures in course 23CSE201T.",
            provenance=ElementProvenance(document_id=doc_id, source_file="nested.docx", structural_index=5),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="nested.docx",
        source_path="/test/nested.docx",
        document_type=".docx",
        file_size_bytes=2048,
        department="Computer Science and Engineering",
        program="B.Tech",
        academic_year="2026-27",
        semester="Semester III",
        regulations=["R23"],
        category="syllabus",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(course_codes=["23CSE201T"]),
    )


def create_fixture_academic_calendar(doc_id: str = "doc_calendar") -> ProcessedDocument:
    """Fixture 3: Academic calendar with exam events and dates."""
    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.HEADING,
            content="## Academic Calendar 2026-27",
            provenance=ElementProvenance(document_id=doc_id, source_file="calendar.txt", line_number=1, structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.PARAGRAPH,
            content="Commencement of Classwork: 10 August 2026.",
            provenance=ElementProvenance(document_id=doc_id, source_file="calendar.txt", line_number=2, structural_index=2),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e3",
            element_type=ElementType.PARAGRAPH,
            content="Mid-Semester Examination I: 12 September 2026 to 16 September 2026.",
            provenance=ElementProvenance(document_id=doc_id, source_file="calendar.txt", line_number=3, structural_index=3),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e4",
            element_type=ElementType.PARAGRAPH,
            content="Mid-Semester Examination II: 10 November 2026 to 14 November 2026.",
            provenance=ElementProvenance(document_id=doc_id, source_file="calendar.txt", line_number=4, structural_index=4),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="calendar.txt",
        source_path="/test/calendar.txt",
        document_type=".txt",
        file_size_bytes=1000,
        academic_year="2026-27",
        category="academic_calendar",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(
            academic_years=["2026-27"],
            examinations=["Mid-Semester Examination I", "Mid-Semester Examination II"],
            dates=["10 August 2026", "12 September 2026 to 16 September 2026", "10 November 2026 to 14 November 2026"],
        ),
    )


def create_fixture_with_small_table(doc_id: str = "doc_small_table") -> ProcessedDocument:
    """Fixture 5: Course syllabus containing an atomic small table."""
    headers = ["Course Code", "Course Title", "Credits"]
    rows = [
        ["23CSE302T", "Natural Language Processing", "3"],
        ["23CSE303T", "Compiler Design", "3"],
        ["23CSE304T", "Cloud Computing", "3"],
    ]
    md_table = "| Course Code | Course Title | Credits |\n| --- | --- | --- |\n" + "\n".join(
        f"| {r[0]} | {r[1]} | {r[2]} |" for r in rows
    )

    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.HEADING,
            content="## Semester VII Course List",
            provenance=ElementProvenance(document_id=doc_id, source_file="courses.docx", page_number=1, structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.TABLE,
            content=md_table,
            provenance=ElementProvenance(document_id=doc_id, source_file="courses.docx", page_number=1, structural_index=2),
            table_data=TableData(headers=headers, rows=rows, num_rows=4, num_cols=3, markdown=md_table),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="courses.docx",
        source_path="/test/courses.docx",
        document_type=".docx",
        file_size_bytes=1500,
        department="Computer Science and Engineering",
        semester="Semester VII",
        regulations=["R23"],
        category="syllabus",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(course_codes=["23CSE302T", "23CSE303T", "23CSE304T"]),
    )


def create_fixture_with_large_table(doc_id: str = "doc_large_table", row_count: int = 40) -> ProcessedDocument:
    """Fixture 6: Exceptionally large table exceeding max tokens that requires row splitting."""
    headers = ["Course Code", "Course Title", "Lecture", "Tutorial", "Practical", "Credits", "Prerequisite"]
    rows = []
    for i in range(1, row_count + 1):
        rows.append([
            f"23CSE{i:03d}T",
            f"Advanced Topics in Computer Science and Engineering Specialization Course {i}",
            "3", "1", "2", "4", "23CSE001T"
        ])

    md_table = "| " + " | ".join(headers) + " |\n| " + " | ".join(["---"] * len(headers)) + " |\n" + "\n".join(
        "| " + " | ".join(r) + " |" for r in rows
    )

    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.HEADING,
            content="## Master Curriculum Table",
            provenance=ElementProvenance(document_id=doc_id, source_file="curriculum.docx", structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.TABLE,
            content=md_table,
            provenance=ElementProvenance(document_id=doc_id, source_file="curriculum.docx", structural_index=2),
            table_data=TableData(headers=headers, rows=rows, num_rows=row_count + 1, num_cols=len(headers), markdown=md_table),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="curriculum.docx",
        source_path="/test/curriculum.docx",
        document_type=".docx",
        file_size_bytes=10000,
        department="Computer Science and Engineering",
        regulations=["R23"],
        category="syllabus",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(regulations=["R23"]),
    )


def create_fixture_multi_page(doc_id: str = "doc_multi_page") -> ProcessedDocument:
    """Fixture 7: Multi-page content with elements distributed across pages 1, 2, and 3."""
    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.HEADING,
            content="## Examination Guidelines",
            provenance=ElementProvenance(document_id=doc_id, source_file="guide.pdf", page_number=1, structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.PARAGRAPH,
            content="Candidates must arrive at the examination hall 15 minutes before the commencement of the exam.",
            provenance=ElementProvenance(document_id=doc_id, source_file="guide.pdf", page_number=1, structural_index=2),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e3",
            element_type=ElementType.PARAGRAPH,
            content="Electronic devices and programmable calculators are strictly prohibited inside the hall under Regulation R23.",
            provenance=ElementProvenance(document_id=doc_id, source_file="guide.pdf", page_number=2, structural_index=3),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e4",
            element_type=ElementType.PARAGRAPH,
            content="Hall tickets must be presented to the invigilator upon request throughout the examination.",
            provenance=ElementProvenance(document_id=doc_id, source_file="guide.pdf", page_number=3, structural_index=4),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="guide.pdf",
        source_path="/test/guide.pdf",
        document_type=".pdf",
        file_size_bytes=3000,
        regulations=["R23"],
        category="exam_guidelines",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(regulations=["R23"]),
    )


def create_fixture_lists(doc_id: str = "doc_lists") -> ProcessedDocument:
    """Fixture 8: Multiple list items under a heading that should preserve list semantics."""
    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.HEADING,
            content="## General Conduct Rules",
            provenance=ElementProvenance(document_id=doc_id, source_file="rules.txt", line_number=1, structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.LIST_ITEM,
            content="1. Minimum 75% attendance is mandatory to appear for End Semester Examinations.",
            provenance=ElementProvenance(document_id=doc_id, source_file="rules.txt", line_number=2, structural_index=2),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e3",
            element_type=ElementType.LIST_ITEM,
            content="2. Condonation of attendance up to 10% on medical grounds requires valid documentation.",
            provenance=ElementProvenance(document_id=doc_id, source_file="rules.txt", line_number=3, structural_index=3),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e4",
            element_type=ElementType.LIST_ITEM,
            content="3. Students below 65% attendance are detained and must repeat the semester.",
            provenance=ElementProvenance(document_id=doc_id, source_file="rules.txt", line_number=4, structural_index=4),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="rules.txt",
        source_path="/test/rules.txt",
        document_type=".txt",
        file_size_bytes=800,
        regulations=["R23"],
        category="exam_guidelines",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(regulations=["R23"]),
    )


def create_fixture_duplicate_content(doc_id: str = "doc_duplicates") -> ProcessedDocument:
    """Fixture 9: Contains exact duplicate paragraphs to verify in-document duplicate detection."""
    repeated_para = "Students must maintain minimum 75 percent attendance under Regulation R23."
    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.HEADING,
            content="## Attendance Notice",
            provenance=ElementProvenance(document_id=doc_id, source_file="dup.txt", line_number=1, structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.PARAGRAPH,
            content=repeated_para,
            provenance=ElementProvenance(document_id=doc_id, source_file="dup.txt", line_number=2, structural_index=2),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e3",
            element_type=ElementType.HEADING,
            content="## Attendance Notice",
            provenance=ElementProvenance(document_id=doc_id, source_file="dup.txt", line_number=3, structural_index=3),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e4",
            element_type=ElementType.PARAGRAPH,
            content=repeated_para,
            provenance=ElementProvenance(document_id=doc_id, source_file="dup.txt", line_number=4, structural_index=4),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="dup.txt",
        source_path="/test/dup.txt",
        document_type=".txt",
        file_size_bytes=600,
        regulations=["R23"],
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(regulations=["R23"]),
    )


def create_fixture_oversized_paragraph(doc_id: str = "doc_oversized") -> ProcessedDocument:
    """Fixture 10: Paragraph exceeding max tokens requiring sentence boundary fallback splitting."""
    # Build 1500+ token paragraph from complete sentences
    sentence = "The student conduct guidelines strictly enforce academic honesty in all laboratory exercises and examinations. "
    huge_paragraph = sentence * 70  # ~1400 tokens

    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.HEADING,
            content="## Code of Conduct",
            provenance=ElementProvenance(document_id=doc_id, source_file="oversized.txt", line_number=1, structural_index=1),
        ),
        DocumentElement(
            element_id=f"{doc_id}_e2",
            element_type=ElementType.PARAGRAPH,
            content=huge_paragraph.strip(),
            provenance=ElementProvenance(document_id=doc_id, source_file="oversized.txt", line_number=2, structural_index=2),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="oversized.txt",
        source_path="/test/oversized.txt",
        document_type=".txt",
        file_size_bytes=8000,
        category="exam_guidelines",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text="\n".join(e.content for e in elements),
        cleaned_text="\n".join(e.content for e in elements),
        academic_structures=DetectedAcademicStructures(),
    )


def create_fixture_missing_metadata(doc_id: str = "doc_missing_meta") -> ProcessedDocument:
    """Fixture 11: Document with missing optional metadata (department, semester, regulation = None)."""
    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.PARAGRAPH,
            content="General announcement regarding library working hours and sports facilities.",
            provenance=ElementProvenance(document_id=doc_id, source_file="announcement.txt", line_number=1, structural_index=1),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="announcement.txt",
        source_path="/test/announcement.txt",
        document_type=".txt",
        file_size_bytes=200,
        department=None,
        program=None,
        academic_year=None,
        semester=None,
        regulations=[],
        category="department_notice",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text=elements[0].content,
        cleaned_text=elements[0].content,
        academic_structures=DetectedAcademicStructures(),
    )


def create_fixture_multi_entity_chunk(doc_id: str = "doc_multi_entity") -> ProcessedDocument:
    """Fixture 12: Single chunk containing multiple academic entities (courses, dates, regulations, exams)."""
    content = (
        "Notice for B.Tech Semester VII: Under Regulation R23 and R20, the Mid-Semester Examination I "
        "for courses 23CSE302T and 20EC201 will take place between 12 September 2026 to 16 September 2026."
    )
    elements = [
        DocumentElement(
            element_id=f"{doc_id}_e1",
            element_type=ElementType.PARAGRAPH,
            content=content,
            provenance=ElementProvenance(document_id=doc_id, source_file="multi_notice.txt", line_number=1, structural_index=1),
        ),
    ]

    meta = DocumentMetadata(
        document_id=doc_id,
        document_name="multi_notice.txt",
        source_path="/test/multi_notice.txt",
        document_type=".txt",
        file_size_bytes=500,
        department="Computer Science and Engineering",
        program="B.Tech",
        academic_year="2026-27",
        semester="Semester VII",
        regulations=["R23", "R20"],
        category="department_notice",
        ingestion_timestamp="2026-09-16T12:00:00Z",
    )

    return ProcessedDocument(
        document_id=doc_id,
        metadata=meta,
        elements=elements,
        raw_elements_count=len(elements),
        raw_text=content,
        cleaned_text=content,
        academic_structures=DetectedAcademicStructures(
            course_codes=["23CSE302T", "20EC201"],
            regulations=["R23", "R20"],
            examinations=["Mid-Semester Examination I"],
            dates=["12 September 2026 to 16 September 2026"],
        ),
    )
