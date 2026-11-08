"""Persistent local vector store backed by SQLite and vectorized NumPy.

Suitable for the SRU Assistant prototype, evaluation, and local deployment.
Extensible to other backends via BaseVectorStore.
"""
from __future__ import annotations



import json
import sqlite3
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import numpy as np

from retrieval.models import (
    IndexManifest,
    VectorRecord,
    VectorSearchResult,
    VectorStoreError,
)
from retrieval.vectorstore.base import BaseVectorStore


class SQLiteVectorStore(BaseVectorStore):
    """Persistent local vector store suitable for the SRU Assistant prototype, evaluation, and local deployment.

    Features:
    - Persistent disk storage via SQLite with WAL mode.
    - Compact float32 BLOB vector storage.
    - SQL pre-filtering on structured metadata fields (department, semester, regulation, academic_year, document_type).
    - Sub-millisecond vectorized cosine similarity computation via NumPy dot-products.
    - Strict tie-breaking (similarity descending, chunk_id ascending) for deterministic search results.
    - Index manifest tracking to prevent model/dimension corruption.
    """

    INDEXED_METADATA_FIELDS = {
        "department",
        "semester",
        "regulation",
        "academic_year",
        "document_type",
    }

    def __init__(self, db_path: str = "./data/vectorstore/sru_vectors.db"):
        self.db_path = str(db_path)
        if self.db_path != ":memory:":
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        # Enable WAL mode for high concurrency and fast writes (only for file-backed DBs)
        if self.db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL;")
            self._conn.execute("PRAGMA synchronous=NORMAL;")
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return self._conn

    def close(self) -> None:
        """Close the database connection."""
        try:
            if hasattr(self, "_conn") and self._conn:
                self._conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            # Manifest table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS index_manifest (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    embedding_provider TEXT NOT NULL,
                    embedding_model TEXT NOT NULL,
                    embedding_dimension INTEGER NOT NULL,
                    distance_metric TEXT NOT NULL,
                    index_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    total_vectors INTEGER NOT NULL
                )
                """
            )

            # Vector records table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS vector_records (
                    chunk_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    text TEXT NOT NULL,
                    chunk_content_hash TEXT NOT NULL,
                    vector BLOB NOT NULL,
                    metadata_json TEXT NOT NULL,
                    provenance_json TEXT NOT NULL,
                    department TEXT,
                    semester TEXT,
                    regulation TEXT,
                    academic_year TEXT,
                    document_type TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            # Indices for fast filtering
            conn.execute("CREATE INDEX IF NOT EXISTS idx_doc_id ON vector_records(document_id);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_dept ON vector_records(department);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_sem ON vector_records(semester);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_reg ON vector_records(regulation);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_year ON vector_records(academic_year);")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON vector_records(document_type);")
            conn.commit()

    def save_manifest(self, manifest: IndexManifest) -> None:
        """Persist or update the index manifest."""
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT INTO index_manifest (
                    id, embedding_provider, embedding_model, embedding_dimension,
                    distance_metric, index_version, created_at, total_vectors
                ) VALUES (1, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    embedding_provider = excluded.embedding_provider,
                    embedding_model = excluded.embedding_model,
                    embedding_dimension = excluded.embedding_dimension,
                    distance_metric = excluded.distance_metric,
                    index_version = excluded.index_version,
                    total_vectors = excluded.total_vectors
                """,
                (
                    manifest.embedding_provider,
                    manifest.embedding_model,
                    manifest.embedding_dimension,
                    manifest.distance_metric,
                    manifest.index_version,
                    manifest.created_at,
                    manifest.total_vectors,
                ),
            )
            conn.commit()

    def get_manifest(self) -> IndexManifest | None:
        """Retrieve the persisted index manifest."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT embedding_provider, embedding_model, embedding_dimension, distance_metric, "
                "index_version, created_at, total_vectors FROM index_manifest WHERE id = 1"
            )
            row = cursor.fetchone()
            if row is None:
                return None
            return IndexManifest(
                embedding_provider=row["embedding_provider"],
                embedding_model=row["embedding_model"],
                embedding_dimension=row["embedding_dimension"],
                distance_metric=row["distance_metric"],
                index_version=row["index_version"],
                created_at=row["created_at"],
                total_vectors=row["total_vectors"],
            )

    def add_records(self, records: Sequence[VectorRecord]) -> int:
        """Insert or replace vector records in the SQLite database."""
        if not records:
            return 0

        rows = []
        for r in records:
            # Pack vector as float32 binary BLOB
            vec_bytes = np.array(r.vector, dtype=np.float32).tobytes()
            meta = r.metadata or {}
            rows.append(
                (
                    r.chunk_id,
                    r.document_id,
                    r.text,
                    r.chunk_content_hash,
                    vec_bytes,
                    json.dumps(meta, ensure_ascii=False),
                    json.dumps(r.provenance or {}, ensure_ascii=False),
                    meta.get("department"),
                    meta.get("semester"),
                    meta.get("regulation"),
                    meta.get("academic_year"),
                    meta.get("document_type"),
                    r.created_at,
                    r.updated_at,
                )
            )

        with self._get_connection() as conn:
            conn.executemany(
                """
                INSERT INTO vector_records (
                    chunk_id, document_id, text, chunk_content_hash, vector,
                    metadata_json, provenance_json, department, semester,
                    regulation, academic_year, document_type, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    document_id = excluded.document_id,
                    text = excluded.text,
                    chunk_content_hash = excluded.chunk_content_hash,
                    vector = excluded.vector,
                    metadata_json = excluded.metadata_json,
                    provenance_json = excluded.provenance_json,
                    department = excluded.department,
                    semester = excluded.semester,
                    regulation = excluded.regulation,
                    academic_year = excluded.academic_year,
                    document_type = excluded.document_type,
                    updated_at = excluded.updated_at
                """,
                rows,
            )
            # Update manifest total_vectors if manifest exists
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM vector_records")
            cnt = cursor.fetchone()["cnt"]
            conn.execute("UPDATE index_manifest SET total_vectors = ? WHERE id = 1", (cnt,))
            conn.commit()

        return len(records)

    def get_record(self, chunk_id: str) -> VectorRecord | None:
        """Fetch a single record by chunk_id."""
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT chunk_id, document_id, text, chunk_content_hash, vector, "
                "metadata_json, provenance_json, created_at, updated_at "
                "FROM vector_records WHERE chunk_id = ?",
                (chunk_id,),
            )
            row = cursor.fetchone()
            if row is None:
                return None
            vector_arr = np.frombuffer(row["vector"], dtype=np.float32).tolist()
            return VectorRecord(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                text=row["text"],
                chunk_content_hash=row["chunk_content_hash"],
                vector=vector_arr,
                metadata=json.loads(row["metadata_json"]),
                provenance=json.loads(row["provenance_json"]),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def delete_records(self, chunk_ids: Sequence[str]) -> int:
        """Delete records matching chunk_ids."""
        if not chunk_ids:
            return 0
        with self._get_connection() as conn:
            placeholders = ",".join("?" for _ in chunk_ids)
            cursor = conn.execute(
                f"DELETE FROM vector_records WHERE chunk_id IN ({placeholders})",
                list(chunk_ids),
            )
            deleted = cursor.rowcount
            # Update count
            cnt_cursor = conn.execute("SELECT COUNT(*) as cnt FROM vector_records")
            cnt = cnt_cursor.fetchone()["cnt"]
            conn.execute("UPDATE index_manifest SET total_vectors = ? WHERE id = 1", (cnt,))
            conn.commit()
            return deleted

    def count(self) -> int:
        """Return total count of indexed vector records."""
        with self._get_connection() as conn:
            cursor = conn.execute("SELECT COUNT(*) as cnt FROM vector_records")
            return int(cursor.fetchone()["cnt"])

    def clear(self) -> None:
        """Remove all vector records and reset count."""
        with self._get_connection() as conn:
            conn.execute("DELETE FROM vector_records")
            conn.execute("UPDATE index_manifest SET total_vectors = 0 WHERE id = 1")
            conn.commit()

    def search(
        self,
        query_vector: Sequence[float],
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """Perform vectorized cosine similarity search with SQL metadata pre-filtering.

        Tie-breaking rule: cosine_similarity descending, then chunk_id ascending.
        """
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        query_arr = np.asarray(query_vector, dtype=np.float32)
        if query_arr.ndim != 1 or query_arr.size == 0:
            raise VectorStoreError("Query vector must be a non-empty 1D float array")

        # Build SQL query with optional metadata pre-filters
        where_clauses = []
        sql_params: list[Any] = []

        if filters:
            for key, val in filters.items():
                if val is None:
                    continue
                if key in self.INDEXED_METADATA_FIELDS:
                    where_clauses.append(f"{key} = ?")
                    sql_params.append(str(val))
                else:
                    # Filter inside JSON metadata
                    where_clauses.append("json_extract(metadata_json, ?) = ?")
                    sql_params.append(f"$.{key}")
                    sql_params.append(val if isinstance(val, (int, float, bool)) else str(val))

        sql = "SELECT chunk_id, document_id, text, vector, metadata_json, provenance_json FROM vector_records"
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        with self._get_connection() as conn:
            cursor = conn.execute(sql, sql_params)
            rows = cursor.fetchall()

        if not rows:
            return []

        # Vectorized batch cosine similarity
        chunk_ids = [r["chunk_id"] for r in rows]
        doc_ids = [r["document_id"] for r in rows]
        texts = [r["text"] for r in rows]
        metadatas = [json.loads(r["metadata_json"]) for r in rows]
        provenances = [json.loads(r["provenance_json"]) for r in rows]

        # Stack vectors into 2D NumPy matrix
        try:
            matrix = np.array([np.frombuffer(r["vector"], dtype=np.float32) for r in rows])
        except Exception as e:
            raise VectorStoreError(f"Failed to unpack binary vector buffer: {e}") from e

        if matrix.shape[1] != query_arr.shape[0]:
            raise VectorStoreError(
                f"Vector dimension mismatch: query is {query_arr.shape[0]}-d, "
                f"stored records are {matrix.shape[1]}-d"
            )

        # Dot product for unit-normalized vectors equals cosine similarity
        raw_similarities = np.dot(matrix, query_arr)

        # Sort indices: similarity descending, tie-break by chunk_id ascending
        ranked_indices = sorted(
            range(len(rows)),
            key=lambda i: (-float(raw_similarities[i]), chunk_ids[i]),
        )

        results: list[VectorSearchResult] = []
        for idx in ranked_indices[:top_k]:
            cos = float(raw_similarities[idx])
            # Clamp to [-1.0, 1.0] against precision overshoot
            clamped_cos = max(-1.0, min(1.0, cos))
            norm_score = round((clamped_cos + 1.0) / 2.0, 6)

            results.append(
                VectorSearchResult(
                    chunk_id=chunk_ids[idx],
                    document_id=doc_ids[idx],
                    text=texts[idx],
                    cosine_similarity=round(clamped_cos, 6),
                    normalized_score=norm_score,
                    metadata=metadatas[idx],
                    provenance=provenances[idx],
                )
            )

        return results
