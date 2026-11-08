"""Idempotent vector indexing pipeline converting structured chunks into vector records."""
from __future__ import annotations


import hashlib
import json
import time
from collections.abc import Sequence
from pathlib import Path

from ingestion.chunking.models import Chunk, ChunkDataset
from retrieval.embeddings.base import BaseEmbeddingModel
from retrieval.models import IndexingReport, IndexManifest, VectorRecord
from retrieval.vectorstore.base import BaseVectorStore


class VectorIndexer:
    """Batch-oriented, idempotent indexing pipeline.


    Features:
    - Tracks SHA-256 chunk_content_hash to detect unchanged vs modified chunks.
    - Completely idempotent: re-indexing unchanged datasets skips re-computation.
    - Auto-updates stale vector records when chunk text has changed.
    - Batches embedding operations for high throughput.
    - Synchronizes and persists the vector index manifest.
    """

    def __init__(self, embedding_model: BaseEmbeddingModel, vector_store: BaseVectorStore):
        self.model = embedding_model
        self.store = vector_store

    @staticmethod
    def compute_content_hash(text: str) -> str:
        """Compute SHA-256 hex digest of chunk text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def index_chunks(
        self,
        chunks: Sequence[Chunk],
        batch_size: int = 32,
    ) -> IndexingReport:
        """Index a sequence of Chunk objects into the vector store.

        - New chunk_id -> embed and insert.
        - Existing chunk_id with matching hash -> skip.
        - Existing chunk_id with differing hash -> re-embed and update.
        """
        start_time = time.perf_counter()
        report = IndexingReport(chunks_requested=len(chunks))

        if not chunks:
            report.elapsed_seconds = round(time.perf_counter() - start_time, 4)
            report.manifest = self.store.get_manifest()
            return report

        # Ensure index manifest is initialized
        current_manifest = self.store.get_manifest()
        if current_manifest is None or current_manifest.total_vectors == 0:
            manifest = IndexManifest(
                embedding_provider=self.model.provider_name,
                embedding_model=self.model.model_name,
                embedding_dimension=self.model.dimension,
                distance_metric="cosine",
                index_version="1.0.0",
                total_vectors=0,
            )
            self.store.save_manifest(manifest)
        else:
            # Validate compatibility before adding records
            self.store.validate_manifest_compatibility(
                self.model.provider_name, self.model.model_name, self.model.dimension
            )

        # Plan work: inspect existing records to identify new vs stale vs unchanged
        chunks_to_embed: list[tuple[Chunk, str, bool]] = []  # (chunk, hash, is_update)

        for chk in chunks:
            content_hash = self.compute_content_hash(chk.text)
            existing = self.store.get_record(chk.chunk_id)

            if existing is None:
                # Brand new chunk
                chunks_to_embed.append((chk, content_hash, False))
            elif existing.chunk_content_hash == content_hash:
                # Content identical, skip
                report.chunks_skipped += 1
            else:
                # Chunk ID exists but content hash differs -> stale vector, re-embed
                chunks_to_embed.append((chk, content_hash, True))

        # Process in batches
        effective_batch_size = max(1, batch_size)
        for i in range(0, len(chunks_to_embed), effective_batch_size):
            batch_slice = chunks_to_embed[i : i + effective_batch_size]
            batch_texts = [item[0].text for item in batch_slice]

            try:
                embeddings = self.model.embed_batch(batch_texts)
            except Exception:
                # Mark this batch as failed
                report.chunks_failed += len(batch_slice)
                continue

            records_to_write: list[VectorRecord] = []
            for (chk, content_hash, is_update), emb in zip(batch_slice, embeddings):
                rec = VectorRecord(
                    chunk_id=chk.chunk_id,
                    document_id=chk.document_id,
                    text=chk.text,
                    chunk_content_hash=content_hash,
                    vector=emb,
                    metadata=chk.metadata.model_dump(),
                    provenance=chk.provenance.model_dump(),
                )
                records_to_write.append(rec)
                if is_update:
                    report.chunks_updated += 1
                else:
                    report.chunks_indexed += 1

            self.store.add_records(records_to_write)

        report.elapsed_seconds = round(time.perf_counter() - start_time, 4)
        report.manifest = self.store.get_manifest()
        return report

    def index_dataset(self, dataset: ChunkDataset, batch_size: int = 32) -> IndexingReport:
        """Index all chunks from a structured ChunkDataset."""
        return self.index_chunks(dataset.chunks, batch_size=batch_size)

    def index_dataset_file(self, dataset_path: str | Path, batch_size: int = 32) -> IndexingReport:
        """Load a ChunkDataset JSON file and index its contents."""
        path = Path(dataset_path)
        if not path.is_file():
            raise FileNotFoundError(f"Chunk dataset file not found: {path}")

        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        dataset = ChunkDataset.model_validate(data)
        return self.index_dataset(dataset, batch_size=batch_size)

    def index_directory(
        self,
        chunks_dir: str | Path,
        batch_size: int = 32,
        glob_pattern: str = "*.json",
    ) -> list[IndexingReport]:
        """Index all chunk dataset files matching glob_pattern in the target directory."""
        directory = Path(chunks_dir)
        if not directory.is_dir():
            return []

        reports: list[IndexingReport] = []
        for file_path in sorted(directory.glob(glob_pattern)):
            try:
                rep = self.index_dataset_file(file_path, batch_size=batch_size)
                reports.append(rep)
            except Exception:
                pass
        return reports
