"""Fixed-window token chunker for experimental baseline comparison (Phase 2 & Phase 9)."""
from __future__ import annotations


from ingestion.chunking.base import BaseChunker
from ingestion.chunking.models import Chunk, ChunkMetadata, ChunkProvenance
from ingestion.chunking.tokenizer import BaseTokenizer, get_default_tokenizer
from ingestion.models import ProcessedDocument
from ingestion.processors.detectors import (
    CourseCodeDetector,
    DateDetector,
    ExaminationDetector,
    RegulationDetector,
)


class FixedWindowChunker(BaseChunker):
    """Experimental baseline chunker using fixed token window with fixed token overlap.


    Does not inspect document structure or headings; strictly segments by token offsets.
    Used as an objective comparison baseline against StructureAwareChunker.
    """

    def __init__(
        self,
        target_tokens: int = 500,
        overlap_tokens: int = 100,
        tokenizer: BaseTokenizer | None = None,
    ) -> None:
        super().__init__(
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens,
            min_tokens=10,
            max_tokens=target_tokens + 50,
            tokenizer=tokenizer or get_default_tokenizer(),
        )
        self.course_detector = CourseCodeDetector()
        self.date_detector = DateDetector()
        self.reg_detector = RegulationDetector()
        self.exam_detector = ExaminationDetector()

    def chunk_document(self, processed_doc: ProcessedDocument) -> list[Chunk]:
        """Split document text into fixed token windows with overlap."""
        tokens = self.tokenizer.tokenize(processed_doc.cleaned_text)
        if not tokens:
            return []

        chunks: list[Chunk] = []
        step = max(1, self.target_tokens - self.overlap_tokens)
        chunk_idx = 0

        # Pre-extract all element provenance for mapping
        all_elements = processed_doc.elements

        for i in range(0, len(tokens), step):
            window_tokens = tokens[i : i + self.target_tokens]
            if not window_tokens:
                break

            chunk_text = " ".join(window_tokens)
            token_count = len(window_tokens)
            word_count = len(chunk_text.split())
            char_count = len(chunk_text)

            # Detect chunk-local entities
            dummy_elem = []
            courses = self.course_detector.detect(dummy_elem, chunk_text)
            dates = self.date_detector.detect(dummy_elem, chunk_text)
            regs = self.reg_detector.detect(dummy_elem, chunk_text)
            exams = self.exam_detector.detect(dummy_elem, chunk_text)

            # Aggregate provenance from all elements (approximated for fixed-window)
            page_numbers = sorted({e.provenance.page_number for e in all_elements if e.provenance.page_number})
            element_ids = [e.element_id for e in all_elements if e.content in chunk_text or chunk_text in e.content]
            if not element_ids and all_elements:
                element_ids = [all_elements[min(chunk_idx, len(all_elements) - 1)].element_id]

            provenance = ChunkProvenance(
                document_id=processed_doc.document_id,
                source_file=processed_doc.metadata.document_name,
                page_numbers=page_numbers,
                line_numbers=[],
                element_ids=element_ids,
            )

            metadata = ChunkMetadata(
                document_id=processed_doc.document_id,
                document_name=processed_doc.metadata.document_name,
                document_type=processed_doc.metadata.document_type,
                department=processed_doc.metadata.department,
                program=processed_doc.metadata.program,
                academic_year=processed_doc.metadata.academic_year,
                semester=processed_doc.metadata.semester,
                category=processed_doc.metadata.category,
                regulations=processed_doc.metadata.regulations,
                section_path="FixedWindow",
                heading_hierarchy=["FixedWindow"],
                chunk_course_codes=courses,
                chunk_dates=dates,
                chunk_regulations=regs,
                chunk_examinations=exams,
            )

            chunks.append(
                Chunk(
                    chunk_id=f"{processed_doc.document_id}_chunk_{chunk_idx:04d}",
                    document_id=processed_doc.document_id,
                    chunk_index=chunk_idx,
                    text=chunk_text,
                    token_count=token_count,
                    char_count=char_count,
                    word_count=word_count,
                    is_table=False,
                    is_oversized=False,
                    metadata=metadata,
                    provenance=provenance,
                )
            )
            chunk_idx += 1

            if i + self.target_tokens >= len(tokens):
                break

        return chunks
