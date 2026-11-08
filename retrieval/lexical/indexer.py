"""Idempotent BM25 indexer with content-hash delta tracking."""
from __future__ import annotations


import hashlib
import time
from collections.abc import Sequence
from pathlib import Path

from app.config.settings import get_settings
from ingestion.chunking.models import Chunk
from retrieval.lexical.bm25 import BM25Index
from retrieval.models import BM25IndexingReport


class BM25Indexer:
    """Batch-oriented, idempotent indexing pipeline for the BM25 inverted index.


    Features:
    - Tracks SHA-256 chunk_content_hash to detect UNCHANGED, MODIFIED, NEW, and REMOVED chunks.
    - Idempotent: re-indexing the same dataset skips unchanged chunks without modification.
    - Automatically removes stale chunks no longer present in the source dataset.
    - Updates and persists index metadata and manifest.
    """

    def __init__(self, index: BM25Index | None = None, index_path: str | Path | None = None):
        settings = get_settings()
        self.index_path = Path(index_path or settings.bm25_index_path)
        self.index = index or BM25Index(k1=settings.bm25_k1, b=settings.bm25_b)

        # Attempt to load existing index if file is present on disk
        if self.index_path.exists() and index is None:
            try:
                self.index.load(self.index_path)
            except Exception:
                # If existing file is invalid/corrupt, start fresh for indexing
                self.index = BM25Index(k1=settings.bm25_k1, b=settings.bm25_b)

    @staticmethod
    def compute_content_hash(text: str) -> str:
        """Compute SHA-256 hex digest of chunk text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def index_chunks(
        self,
        chunks: Sequence[Chunk],
        force_rebuild: bool = False,
        prune_missing: bool = True,
    ) -> BM25IndexingReport:
        """Index a sequence of Chunk objects into the BM25 index.

        Delta state management:
        - UNCHANGED: same chunk_id + same content hash -> skip
        - MODIFIED: same chunk_id + different content hash -> update
        - NEW: new chunk_id -> index
        - REMOVED: chunk existed in index but missing from input -> prune (if prune_missing=True)
        """
        start_time = time.perf_counter()
        report = BM25IndexingReport(chunks_requested=len(chunks))

        if force_rebuild:
            # Reset index completely
            self.index = BM25Index(
                tokenizer=self.index.tokenizer,
                k1=self.index.k1,
                b=self.index.b,
            )

        submitted_chunk_ids = set()
        chunk_hashes: list[str] = []

        for chk in chunks:
            submitted_chunk_ids.add(chk.chunk_id)
            content_hash = self.compute_content_hash(chk.text)
            chunk_hashes.append(content_hash)

            meta_dict = chk.metadata.model_dump() if hasattr(chk.metadata, "model_dump") else dict(chk.metadata or {})
            prov_dict = (
                chk.provenance.model_dump() if hasattr(chk.provenance, "model_dump") else dict(chk.provenance or {})
            )

            status = self.index.add_or_update_chunk(
                chunk_id=chk.chunk_id,
                document_id=chk.document_id,
                text=chk.text,
                chunk_content_hash=content_hash,
                metadata=meta_dict,
                provenance=prov_dict,
            )

            if status == "UNCHANGED":
                report.chunks_skipped += 1
            elif status == "MODIFIED":
                report.chunks_updated += 1
            elif status == "NEW":
                report.chunks_indexed += 1

        # Check for REMOVED chunks (chunks previously indexed but absent in current run)
        if prune_missing:
            existing_ids = list(self.index.doc_records.keys())
            for existing_id in existing_ids:
                if existing_id not in submitted_chunk_ids:
                    if self.index.remove_chunk(existing_id):
                        report.chunks_removed += 1

        # Compute aggregate corpus content hash
        sorted_hashes = sorted(chunk_hashes)
        combined_hash = hashlib.sha256("".join(sorted_hashes).encode("utf-8")).hexdigest()
        self.index.source_content_hash = combined_hash

        # Persist index
        self.index.save(self.index_path)

        report.elapsed_seconds = round(time.perf_counter() - start_time, 4)
        report.manifest = self.index.get_manifest()
        return report
