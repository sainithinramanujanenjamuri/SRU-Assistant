"""Mathematically rigorous, zero-dependency BM25 implementation for SRU Assistant.

Implements BM25Okapi scoring with Robertson/Spärck Jones non-negative IDF,
document length normalization, content-hash delta indexing, and deterministic tie-breaking.
"""
from __future__ import annotations



import json
import math
from collections import Counter
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from app.config.settings import get_settings
from retrieval.base import BaseRetriever
from retrieval.lexical.tokenizer import AcademicLexicalTokenizer
from retrieval.models import (
    BM25CorruptionError,
    BM25IndexError,
    BM25IndexManifest,
    IndexCompatibilityError,
    LexicalSearchResult,
)


class BM25Index:
    """In-memory inverted index supporting BM25Okapi scoring and JSON persistence.

    Formulation:
        IDF(t) = ln((N - df(t) + 0.5) / (df(t) + 0.5) + 1)
        BM25(D, Q) = sum(IDF(t) * (tf(t, D) * (k1 + 1)) / (tf(t, D) + k1 * (1 - b + b * |D| / avgdl)))
    """

    INDEX_VERSION = "1.0.0"

    def __init__(
        self,
        tokenizer: AcademicLexicalTokenizer | None = None,
        k1: float = 1.5,
        b: float = 0.75,
    ):
        if k1 <= 0.0:
            raise ValueError(f"k1 must be positive, got {k1}")
        if not (0.0 <= b <= 1.0):
            raise ValueError(f"b must be between 0.0 and 1.0, got {b}")

        self.tokenizer = tokenizer or AcademicLexicalTokenizer()
        self.k1 = k1
        self.b = b

        # Postings structure: term -> {chunk_id: term_frequency}
        self.postings: dict[str, dict[str, int]] = {}
        # Document length: chunk_id -> token_count
        self.doc_lengths: dict[str, int] = {}
        # Document records: chunk_id -> record dictionary
        self.doc_records: dict[str, dict[str, Any]] = {}
        # Aggregated corpus content hash
        self.source_content_hash: str = ""

    @property
    def total_chunks(self) -> int:
        """Total number of document chunks currently indexed."""
        return len(self.doc_records)

    @property
    def vocabulary_size(self) -> int:
        """Total number of unique terms in the inverted index."""
        return len(self.postings)

    @property
    def average_document_length(self) -> float:
        """Average token length across indexed chunks (avgdl)."""
        if not self.doc_lengths:
            return 0.0
        return sum(self.doc_lengths.values()) / len(self.doc_lengths)

    def compute_idf(self, term: str) -> float:
        """Compute Robertson/Spärck Jones non-negative IDF for a term.

        Formula: ln((N - df + 0.5) / (df + 0.5) + 1)
        Guaranteed to be strictly positive (> 0.0) for any df <= N.
        """
        N = self.total_chunks
        if N == 0 or term not in self.postings:
            return 0.0

        df = len(self.postings[term])
        # Non-negative smoothing formula
        val = (N - df + 0.5) / (df + 0.5) + 1.0
        return math.log(max(val, 1e-9))

    def add_or_update_chunk(
        self,
        chunk_id: str,
        document_id: str,
        text: str,
        chunk_content_hash: str,
        metadata: dict[str, Any] | None = None,
        provenance: dict[str, Any] | None = None,
    ) -> str:
        """Add a new chunk or update an existing chunk if content hash changed.

        Returns status string: 'UNCHANGED', 'MODIFIED', or 'NEW'.
        """
        existing = self.doc_records.get(chunk_id)
        if existing is not None:
            if existing.get("chunk_content_hash") == chunk_content_hash:
                return "UNCHANGED"
            # Modified: remove previous postings for this chunk
            self.remove_chunk(chunk_id)
            status = "MODIFIED"
        else:
            status = "NEW"

        tokens = self.tokenizer.tokenize(text)
        doc_len = len(tokens)
        tf_counter = Counter(tokens)

        # Update postings
        for term, freq in tf_counter.items():
            if term not in self.postings:
                self.postings[term] = {}
            self.postings[term][chunk_id] = freq

        self.doc_lengths[chunk_id] = doc_len
        self.doc_records[chunk_id] = {
            "chunk_id": chunk_id,
            "document_id": document_id,
            "text": text,
            "chunk_content_hash": chunk_content_hash,
            "metadata": metadata or {},
            "provenance": provenance or {},
        }
        return status

    def remove_chunk(self, chunk_id: str) -> bool:
        """Remove a chunk from the index. Returns True if removed, False if not found."""
        if chunk_id not in self.doc_records:
            return False

        # Remove from postings
        terms_to_clean = []
        for term, chunk_map in self.postings.items():
            if chunk_id in chunk_map:
                del chunk_map[chunk_id]
                if not chunk_map:
                    terms_to_clean.append(term)

        for term in terms_to_clean:
            del self.postings[term]

        del self.doc_lengths[chunk_id]
        del self.doc_records[chunk_id]
        return True

    def get_manifest(self) -> BM25IndexManifest:
        """Generate manifest summarizing the current state of the index."""
        return BM25IndexManifest(
            index_version=self.INDEX_VERSION,
            tokenizer_version=self.tokenizer.version,
            vocabulary_size=self.vocabulary_size,
            total_chunks=self.total_chunks,
            average_document_length=round(self.average_document_length, 4),
            k1=self.k1,
            b=self.b,
            source_content_hash=self.source_content_hash,
        )

    def score_query(self, query_tokens: Sequence[str], chunk_ids: set[str] | None = None) -> dict[str, float]:
        """Compute raw BM25 scores for the given query tokens across candidate chunks."""
        scores: dict[str, float] = {}
        if not query_tokens or self.total_chunks == 0:
            return scores

        avgdl = max(self.average_document_length, 1e-6)
        candidates = chunk_ids if chunk_ids is not None else set(self.doc_records.keys())

        # Collect unique terms in query and compute their IDF
        term_idfs = {term: self.compute_idf(term) for term in query_tokens}

        for term in query_tokens:
            idf = term_idfs.get(term, 0.0)
            if idf <= 0.0 or term not in self.postings:
                continue

            posting_map = self.postings[term]
            for doc_id, tf in posting_map.items():
                if doc_id not in candidates:
                    continue

                doc_len = self.doc_lengths.get(doc_id, 0)
                # BM25 term saturation formula
                denom = tf + self.k1 * (1.0 - self.b + self.b * (doc_len / avgdl))
                if denom > 0:
                    term_score = idf * (tf * (self.k1 + 1.0)) / denom
                    scores[doc_id] = scores.get(doc_id, 0.0) + term_score

        return scores

    def save(self, filepath: str | Path) -> None:
        """Serialize index and manifest to a JSON file."""
        target_path = Path(filepath)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        manifest = self.get_manifest()
        payload = {
            "manifest": manifest.model_dump(),
            "postings": self.postings,
            "doc_lengths": self.doc_lengths,
            "doc_records": self.doc_records,
            "source_content_hash": self.source_content_hash,
        }

        temp_path = target_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
            temp_path.replace(target_path)
        except Exception as e:
            if temp_path.exists():
                temp_path.unlink()
            raise BM25IndexError(f"Failed to persist BM25 index to '{filepath}': {e}") from e

    def load(self, filepath: str | Path) -> None:
        """Load index from JSON file and validate manifest compatibility."""
        target_path = Path(filepath)
        if not target_path.exists():
            raise BM25IndexError(f"BM25 index file not found at '{filepath}'. Index rebuild required.")

        try:
            with open(target_path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise BM25CorruptionError(f"BM25 index file at '{filepath}' is corrupt or invalid JSON: {e}") from e

        if not isinstance(data, dict) or "manifest" not in data or "postings" not in data:
            raise BM25CorruptionError(f"BM25 index at '{filepath}' is missing mandatory schema keys.")

        try:
            manifest = BM25IndexManifest(**data["manifest"])
        except Exception as e:
            raise BM25CorruptionError(f"BM25 manifest at '{filepath}' failed validation: {e}") from e

        # Validate compatibility with current runtime tokenizer and BM25 parameters
        compatible, reason = manifest.is_compatible_with(
            tokenizer_version=self.tokenizer.version,
            k1=self.k1,
            b=self.b,
        )
        if not compatible:
            raise IndexCompatibilityError(
                f"BM25 index compatibility error for '{filepath}': {reason}. Re-run indexer with --force-rebuild."
            )

        self.postings = data.get("postings", {})
        self.doc_lengths = data.get("doc_lengths", {})
        self.doc_records = data.get("doc_records", {})
        self.source_content_hash = data.get("source_content_hash", "")


class BM25Retriever(BaseRetriever):
    """Lexical keyword retriever using BM25Okapi scoring.

    Features:
    - Metadata pre-filtering matching Phase 3 VectorRetriever fields.
    - Min-max score normalization with division-by-zero protection.
    - Deterministic tie-breaking: bm25_score DESC, chunk_id ASC.
    """

    retrieval_mode: str = "lexical"

    def __init__(self, index: BM25Index):
        self.index = index

    @classmethod
    def from_file(
        cls,
        index_path: str | Path | None = None,
        k1: float | None = None,
        b: float | None = None,
    ) -> "BM25Retriever":
        """Instantiate BM25Retriever by loading a persisted index file."""
        settings = get_settings()
        path = index_path or settings.bm25_index_path
        k1_val = k1 if k1 is not None else settings.bm25_k1
        b_val = b if b is not None else settings.bm25_b

        bm25_index = BM25Index(k1=k1_val, b=b_val)
        bm25_index.load(path)
        return cls(bm25_index)

    def _matches_filters(self, metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
        """Check if chunk metadata satisfies all specified filter criteria."""
        for key, expected_val in filters.items():
            if expected_val is None:
                continue
            actual_val = metadata.get(key)
            if actual_val is None or str(actual_val).lower() != str(expected_val).lower():
                return False
        return True

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
    ) -> list[LexicalSearchResult]:
        """Execute lexical keyword search with metadata pre-filtering.

        Args:
            query: Non-empty query string.
            top_k: Positive number of results to return.
            filters: Optional dictionary of metadata criteria.

        Returns:
            Ranked list of LexicalSearchResult objects.
        """
        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        if self.index.total_chunks == 0:
            return []

        # 1. Metadata pre-filtering
        all_doc_records = self.index.doc_records
        if filters:
            candidate_ids = {
                chunk_id
                for chunk_id, record in all_doc_records.items()
                if self._matches_filters(record.get("metadata", {}), filters)
            }
        else:
            candidate_ids = set(all_doc_records.keys())

        if not candidate_ids:
            return []

        # 2. Tokenize query
        query_tokens = self.index.tokenizer.tokenize(query)
        if not query_tokens:
            return []

        # 3. Compute BM25 scores
        scores = self.index.score_query(query_tokens, candidate_ids)
        if not scores:
            return []

        # Filter to candidates with positive scores
        scored_candidates = [(doc_id, score) for doc_id, score in scores.items() if score > 0.0]
        if not scored_candidates:
            return []

        # 4. Deterministic sorting: bm25_score DESC, chunk_id ASC
        scored_candidates.sort(key=lambda item: (-item[1], item[0]))

        # Truncate to top_k
        top_candidates = scored_candidates[:top_k]

        # 5. Min-max score normalization per query
        max_score = top_candidates[0][1]
        min_score = top_candidates[-1][1]
        score_span = max_score - min_score

        results: list[LexicalSearchResult] = []
        for rank, (chunk_id, raw_score) in enumerate(top_candidates, start=1):
            if score_span > 1e-9:
                norm_score = round((raw_score - min_score) / score_span, 6)
            else:
                # All candidates have identical score; normalize deterministically to 1.0
                norm_score = 1.0 if raw_score > 0.0 else 0.0

            record = all_doc_records[chunk_id]
            results.append(
                LexicalSearchResult(
                    chunk_id=chunk_id,
                    document_id=record["document_id"],
                    text=record["text"],
                    bm25_score=round(raw_score, 6),
                    normalized_score=norm_score,
                    rank=rank,
                    metadata=record.get("metadata", {}),
                    provenance=record.get("provenance", {}),
                )
            )

        return results
