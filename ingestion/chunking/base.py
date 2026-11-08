"""Base chunker abstraction for SRU Assistant (Phase 2)."""
from __future__ import annotations


from abc import ABC, abstractmethod

from ingestion.chunking.models import Chunk, DuplicateChunkReport
from ingestion.chunking.tokenizer import BaseTokenizer, get_default_tokenizer
from ingestion.models import ProcessedDocument


class BaseChunker(ABC):
    """Abstract base class for all chunking strategies."""


    def __init__(
        self,
        target_tokens: int = 500,
        overlap_tokens: int = 100,
        min_tokens: int = 50,
        max_tokens: int = 1200,
        tokenizer: BaseTokenizer | None = None,
    ) -> None:
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.min_tokens = min_tokens
        self.max_tokens = max_tokens
        self.tokenizer = tokenizer or get_default_tokenizer()

    @abstractmethod
    def chunk_document(self, processed_doc: ProcessedDocument) -> list[Chunk]:
        """Transform a ProcessedDocument into a list of coherent, retrieval-ready chunks."""

    @staticmethod
    def detect_in_document_duplicates(chunks: list[Chunk]) -> list[DuplicateChunkReport]:
        """Detect exact duplicate chunk texts within the document's chunks without deleting them."""
        text_to_chunk_ids: dict[str, list[str]] = {}
        for c in chunks:
            clean_t = c.text.strip()
            text_to_chunk_ids.setdefault(clean_t, []).append(c.chunk_id)

        reports: list[DuplicateChunkReport] = []
        for text, ids in text_to_chunk_ids.items():
            if len(ids) > 1:
                snippet = text[:80] + ("..." if len(text) > 80 else "")
                reports.append(
                    DuplicateChunkReport(
                        chunk_ids=ids,
                        text_snippet=snippet,
                        occurrences=len(ids),
                    )
                )

        return reports
