"""Structure-aware chunking strategy respecting headings, tables, lists, and sentences."""
from __future__ import annotations


import re
from typing import Any

from ingestion.chunking.base import BaseChunker
from ingestion.chunking.models import Chunk, ChunkMetadata, ChunkProvenance
from ingestion.chunking.tokenizer import BaseTokenizer, get_default_tokenizer
from ingestion.models import (
    DocumentElement,
    ElementProvenance,
    ElementType,
    ProcessedDocument,
)
from ingestion.processors.detectors import (
    CourseCodeDetector,
    DateDetector,
    ExaminationDetector,
    RegulationDetector,
)


class StructureAwareChunker(BaseChunker):
    """Chunks documents while strictly prioritizing semantic and structural boundaries.


    Hierarchy: Heading -> Subheading -> Table/List -> Paragraph -> Sentence -> Token.
    Tables and lists are preserved atomically where size allows, or split cleanly by rows/items.
    """

    SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+")

    def __init__(
        self,
        target_tokens: int = 500,
        overlap_tokens: int = 100,
        min_tokens: int = 50,
        max_tokens: int = 1200,
        tokenizer: BaseTokenizer | None = None,
    ) -> None:
        super().__init__(
            target_tokens=target_tokens,
            overlap_tokens=overlap_tokens,
            min_tokens=min_tokens,
            max_tokens=max_tokens,
            tokenizer=tokenizer or get_default_tokenizer(),
        )
        self.course_detector = CourseCodeDetector()
        self.date_detector = DateDetector()
        self.reg_detector = RegulationDetector()
        self.exam_detector = ExaminationDetector()

    @staticmethod
    def _estimate_heading_level(element: DocumentElement) -> int:
        """Infer heading level (1 for top-level, 2 for sub-level, etc.)."""
        content = element.content.strip()
        if content.startswith("###"):
            return 3
        if content.startswith("##"):
            return 2
        if content.startswith("#"):
            return 1

        style = str(element.metadata.get("style", "")).lower()
        if "title" in style or "heading 1" in style:
            return 1
        if "heading 2" in style:
            return 2
        if "heading 3" in style:
            return 3

        if element.element_type == ElementType.TITLE:
            return 1
        return 2

    def _extract_chunk_local_entities(self, text: str) -> tuple[list[str], list[str], list[str], list[str]]:
        """Detect entities appearing directly within this chunk's text."""
        dummy_elem = [DocumentElement(
            element_id="temp",
            content=text,
            provenance=ElementProvenance(document_id="temp", source_file="temp"),
        )]
        courses = self.course_detector.detect(dummy_elem, text)
        dates = self.date_detector.detect(dummy_elem, text)
        regs = self.reg_detector.detect(dummy_elem, text)
        exams = self.exam_detector.detect(dummy_elem, text)
        return courses, dates, regs, exams

    def _build_chunk(
        self,
        text: str,
        elements: list[DocumentElement],
        processed_doc: ProcessedDocument,
        chunk_idx: int,
        section_path: str,
        heading_hierarchy: list[str],
        is_table: bool = False,
        table_metadata: dict[str, Any] | None = None,
        is_oversized: bool = False,
    ) -> Chunk:
        """Assemble a validated Chunk with complete provenance and metadata."""
        token_count = self.tokenizer.count_tokens(text)
        word_count = len(text.split())
        char_count = len(text)

        # Aggregate provenance
        page_numbers: set[int] = set()
        line_numbers: set[int] = set()
        element_ids: list[str] = []

        for e in elements:
            if e.element_id not in element_ids:
                element_ids.append(e.element_id)
            if e.provenance.page_number is not None:
                page_numbers.add(e.provenance.page_number)
            if e.provenance.line_number is not None:
                line_numbers.add(e.provenance.line_number)

        provenance = ChunkProvenance(
            document_id=processed_doc.document_id,
            source_file=processed_doc.metadata.document_name,
            page_numbers=sorted(page_numbers),
            line_numbers=sorted(line_numbers),
            element_ids=element_ids,
        )

        courses, dates, regs, exams = self._extract_chunk_local_entities(text)

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
            section_path=section_path,
            heading_hierarchy=list(heading_hierarchy),
            chunk_course_codes=courses,
            chunk_dates=dates,
            chunk_regulations=regs,
            chunk_examinations=exams,
        )

        return Chunk(
            chunk_id=f"{processed_doc.document_id}_chunk_{chunk_idx:04d}",
            document_id=processed_doc.document_id,
            chunk_index=chunk_idx,
            text=text.strip(),
            token_count=token_count,
            char_count=char_count,
            word_count=word_count,
            is_table=is_table,
            is_oversized=is_oversized,
            metadata=metadata,
            provenance=provenance,
            table_metadata=table_metadata,
        )

    def _split_oversized_table(
        self,
        table_elem: DocumentElement,
        processed_doc: ProcessedDocument,
        start_chunk_idx: int,
        section_path: str,
        heading_hierarchy: list[str],
    ) -> list[Chunk]:
        """Split a large table by complete rows while repeating headers in every chunk."""
        table_data = table_elem.table_data
        if not table_data or not table_data.rows:
            # Fallback if no structured grid
            return [
                self._build_chunk(
                    text=table_elem.content,
                    elements=[table_elem],
                    processed_doc=processed_doc,
                    chunk_idx=start_chunk_idx,
                    section_path=section_path,
                    heading_hierarchy=heading_hierarchy,
                    is_table=True,
                    is_oversized=True,
                )
            ]

        headers = table_data.headers
        col_count = len(headers) if headers else 1
        header_line = "| " + " | ".join(h.replace("\n", " ").strip() for h in headers) + " |"
        sep_line = "| " + " | ".join(["---"] * col_count) + " |"
        base_header_text = f"{header_line}\n{sep_line}"
        base_header_tokens = self.tokenizer.count_tokens(base_header_text)

        chunks: list[Chunk] = []
        current_rows: list[list[str]] = []
        current_tokens = base_header_tokens
        chunk_counter = start_chunk_idx
        row_start_idx = 0

        for r_idx, row in enumerate(table_data.rows):
            padded_row = (row + [""] * col_count)[:col_count]
            row_str = "| " + " | ".join(c.replace("\n", " ").strip() for c in padded_row) + " |"
            row_tokens = self.tokenizer.count_tokens(row_str)

            if current_tokens + row_tokens > self.max_tokens and current_rows:
                # Flush current table chunk
                table_text = base_header_text + "\n" + "\n".join(
                    "| " + " | ".join(c.replace("\n", " ").strip() for c in r) + " |" for r in current_rows
                )
                chunks.append(
                    self._build_chunk(
                        text=table_text,
                        elements=[table_elem],
                        processed_doc=processed_doc,
                        chunk_idx=chunk_counter,
                        section_path=section_path,
                        heading_hierarchy=heading_hierarchy,
                        is_table=True,
                        table_metadata={
                            "original_element_id": table_elem.element_id,
                            "split": True,
                            "row_start": row_start_idx,
                            "row_end": r_idx,
                            "total_rows": len(table_data.rows),
                        },
                    )
                )
                chunk_counter += 1
                current_rows = []
                current_tokens = base_header_tokens
                row_start_idx = r_idx

            current_rows.append(padded_row)
            current_tokens += row_tokens

        if current_rows:
            table_text = base_header_text + "\n" + "\n".join(
                "| " + " | ".join(c.replace("\n", " ").strip() for c in r) + " |" for r in current_rows
            )
            chunks.append(
                self._build_chunk(
                    text=table_text,
                    elements=[table_elem],
                    processed_doc=processed_doc,
                    chunk_idx=chunk_counter,
                    section_path=section_path,
                    heading_hierarchy=heading_hierarchy,
                    is_table=True,
                    table_metadata={
                        "original_element_id": table_elem.element_id,
                        "split": True,
                        "row_start": row_start_idx,
                        "row_end": len(table_data.rows),
                        "total_rows": len(table_data.rows),
                    },
                )
            )

        return chunks

    def chunk_document(self, processed_doc: ProcessedDocument) -> list[Chunk]:
        """Chunk document adhering to structural hierarchy, table atomicity, and token limits."""
        chunks: list[Chunk] = []
        heading_stack: list[tuple[int, str]] = []  # (level, title)

        current_elements: list[DocumentElement] = []
        current_texts: list[str] = []
        current_token_count = 0

        def get_current_section() -> tuple[str, list[str]]:
            hierarchy = [title for _, title in heading_stack]
            path = " > ".join(hierarchy) if hierarchy else ""
            return path, hierarchy

        def flush_accumulator() -> None:
            nonlocal current_elements, current_texts, current_token_count
            if not current_texts:
                return

            chunk_text = "\n\n".join(current_texts).strip()
            if not chunk_text:
                current_elements = []
                current_texts = []
                current_token_count = 0
                return

            sec_path, hierarchy = get_current_section()
            new_chunk = self._build_chunk(
                text=chunk_text,
                elements=list(current_elements),
                processed_doc=processed_doc,
                chunk_idx=len(chunks),
                section_path=sec_path,
                heading_hierarchy=hierarchy,
                is_table=False,
                is_oversized=(current_token_count > self.max_tokens),
            )
            chunks.append(new_chunk)

            current_elements = []
            current_texts = []
            current_token_count = 0

        for elem in processed_doc.elements:
            # 1. Heading Elements: Update hierarchy stack and flush if appropriate
            if elem.element_type in (ElementType.TITLE, ElementType.HEADING):
                level = self._estimate_heading_level(elem)
                has_substantive_content = any(
                    e.element_type not in (ElementType.TITLE, ElementType.HEADING)
                    for e in current_elements
                )
                # Flush previous accumulated content when entering a new heading of equal or higher level
                if has_substantive_content and (
                    not heading_stack
                    or level <= heading_stack[-1][0]
                    or current_token_count >= self.min_tokens
                ):
                    flush_accumulator()

                # Pop headings of equal or deeper level
                while heading_stack and heading_stack[-1][0] >= level:
                    heading_stack.pop()

                clean_title = elem.content.lstrip("# ").strip()
                heading_stack.append((level, clean_title))

                # Add heading to the next chunk so context is retained
                current_elements.append(elem)
                current_texts.append(f"### {clean_title}")
                current_token_count += self.tokenizer.count_tokens(clean_title) + 2
                continue

            # 2. Table Elements: Handle atomically or split by rows
            if elem.element_type == ElementType.TABLE:
                # Flush existing accumulated paragraphs before table
                flush_accumulator()

                sec_path, hierarchy = get_current_section()
                tbl_tokens = self.tokenizer.count_tokens(elem.content)

                if tbl_tokens <= self.max_tokens:
                    # Keep whole table as single atomic chunk
                    tbl_chunk = self._build_chunk(
                        text=elem.content,
                        elements=[elem],
                        processed_doc=processed_doc,
                        chunk_idx=len(chunks),
                        section_path=sec_path,
                        heading_hierarchy=hierarchy,
                        is_table=True,
                        table_metadata={
                            "original_element_id": elem.element_id,
                            "split": False,
                            "num_rows": elem.table_data.num_rows if elem.table_data else 0,
                        },
                    )
                    chunks.append(tbl_chunk)
                else:
                    # Oversized table: split cleanly by rows
                    table_split_chunks = self._split_oversized_table(
                        table_elem=elem,
                        processed_doc=processed_doc,
                        start_chunk_idx=len(chunks),
                        section_path=sec_path,
                        heading_hierarchy=hierarchy,
                    )
                    chunks.extend(table_split_chunks)
                continue

            # 3. Regular Paragraphs / List Items
            elem_tokens = self.tokenizer.count_tokens(elem.content)

            # Check if this single element is oversized (exceeds max_tokens)
            if elem_tokens > self.max_tokens:
                flush_accumulator()
                # Split oversized paragraph at sentence boundaries
                sentences = [s.strip() for s in self.SENTENCE_SPLIT_REGEX.split(elem.content) if s.strip()]
                sent_accum: list[str] = []
                sent_tokens = 0

                for sent in sentences:
                    s_tok = self.tokenizer.count_tokens(sent)
                    if sent_tokens + s_tok > self.target_tokens and sent_accum:
                        sec_path, hierarchy = get_current_section()
                        chunks.append(
                            self._build_chunk(
                                text=" ".join(sent_accum),
                                elements=[elem],
                                processed_doc=processed_doc,
                                chunk_idx=len(chunks),
                                section_path=sec_path,
                                heading_hierarchy=hierarchy,
                            )
                        )
                        sent_accum = []
                        sent_tokens = 0

                    sent_accum.append(sent)
                    sent_tokens += s_tok

                if sent_accum:
                    sec_path, hierarchy = get_current_section()
                    chunks.append(
                        self._build_chunk(
                            text=" ".join(sent_accum),
                            elements=[elem],
                            processed_doc=processed_doc,
                            chunk_idx=len(chunks),
                            section_path=sec_path,
                            heading_hierarchy=hierarchy,
                        )
                    )
                continue

            # If adding this element exceeds target size and current accumulator meets minimum size
            if current_token_count + elem_tokens > self.target_tokens and current_token_count >= self.min_tokens:
                flush_accumulator()

            current_elements.append(elem)
            current_texts.append(elem.content)
            current_token_count += elem_tokens

        # Flush any remaining elements
        flush_accumulator()

        return chunks
