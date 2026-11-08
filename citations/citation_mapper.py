"""Citation mapping and provenance extraction connecting claims to retrieved evidence chunks."""
from __future__ import annotations


import re
from typing import Any

from citations.models import CitationItem, ClaimItem
from generation.grounding.entities import AcademicEntityExtractor
from generation.models import RetrievedEvidence


class CitationMapper:
    """Maps discrete factual claims to supporting retrieved evidence chunks and creates structured citations.


    Guarantees:
    - Never fabricates page numbers, section names, document names, or source names (agent.md line 494).
    - Preserves exact provenance: Document -> Page -> Section -> Chunk -> Retrieved Evidence -> Claim -> Citation.
    - Assigns stable, deterministic sequential citation IDs ('1', '2', '3'...) without duplicates.
    - Reuses citations when the same evidence chunk supports multiple claims.
    - Supports multi-chunk and multi-document claim mapping.
    - Leaves unsupported claims un-cited (is_supported=False) rather than falsely attributing nearest chunks.
    """

    STOPWORDS = {
        "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with",
        "by", "about", "as", "into", "through", "during", "before", "after", "above",
        "below", "from", "up", "down", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "of", "this", "that",
        "these", "those", "it", "its", "they", "them", "their", "will", "would",
        "shall", "should", "may", "might", "must", "can", "could", "also", "each",
        "all", "any", "both", "such", "not", "only", "same", "so", "than", "too",
    }

    def __init__(self, min_match_score: float = 0.40) -> None:
        self.min_match_score = min_match_score

    def map_claims_to_evidence(
        self,
        claims: list[ClaimItem],
        evidence_items: list[RetrievedEvidence],
    ) -> tuple[list[ClaimItem], list[CitationItem]]:
        """Map extracted claims against surviving evidence chunks and return updated claims and citations."""
        if not claims or not evidence_items:
            return claims, []

        # Index candidate evidence chunks by chunk_id
        chunk_by_id: dict[str, RetrievedEvidence] = {ev.chunk_id: ev for ev in evidence_items}

        # Track allocated citations: chunk_id -> (citation_id, CitationItem)
        chunk_to_citation_id: dict[str, str] = {}
        citations_ordered: list[CitationItem] = []
        next_citation_num = 1

        updated_claims: list[ClaimItem] = []

        for claim in claims:
            # Find matching evidence chunks for this claim
            matched_chunk_scores: list[tuple[str, float]] = []

            for ev in evidence_items:
                score = self._compute_claim_evidence_match(claim, ev)
                if score >= self.min_match_score:
                    matched_chunk_scores.append((ev.chunk_id, score))

            # Sort descending by match score
            matched_chunk_scores.sort(key=lambda x: x[1], reverse=True)

            if not matched_chunk_scores:
                # Unsupported claim - do NOT attach misleading citation
                updated_claims.append(
                    claim.model_copy(
                        update={
                            "is_supported": False,
                            "associated_citation_ids": [],
                            "support_evidence_chunk_ids": [],
                            "support_score": 0.0,
                        }
                    )
                )
                continue

            # Associate citation IDs (reuse existing citation for this chunk if already created)
            associated_citation_ids: list[str] = []
            support_chunk_ids: list[str] = []
            best_score = matched_chunk_scores[0][1]

            for chunk_id, _ in matched_chunk_scores:
                support_chunk_ids.append(chunk_id)
                if chunk_id in chunk_to_citation_id:
                    cit_id = chunk_to_citation_id[chunk_id]
                else:
                    cit_id = str(next_citation_num)
                    next_citation_num += 1
                    chunk_to_citation_id[chunk_id] = cit_id

                    # Create new CitationItem for this evidence chunk
                    ev_item = chunk_by_id[chunk_id]
                    cit_item = self._create_citation_item(
                        citation_id=cit_id,
                        evidence=ev_item,
                        claim_text=claim.claim_text,
                    )
                    citations_ordered.append(cit_item)

                if cit_id not in associated_citation_ids:
                    associated_citation_ids.append(cit_id)

            updated_claims.append(
                claim.model_copy(
                    update={
                        "is_supported": True,
                        "associated_citation_ids": associated_citation_ids,
                        "support_evidence_chunk_ids": support_chunk_ids,
                        "support_score": round(best_score, 4),
                    }
                )
            )

        return updated_claims, citations_ordered

    def extract_provenance(self, evidence: RetrievedEvidence) -> dict[str, Any]:
        """Extract validated provenance fields without hallucinating missing metadata."""
        doc_id = evidence.document_id
        doc_name = evidence.document_name or "Unknown Document"

        # Extract page number accurately
        page_num: int | None = None
        page_str = "p. N/A"

        # 1. Check metadata dictionary for explicit integer page_number
        meta_page = evidence.metadata.get("page_number") or evidence.metadata.get("page")
        if isinstance(meta_page, int) and meta_page > 0:
            page_num = meta_page
            page_str = f"p. {page_num}"
        elif isinstance(meta_page, str) and meta_page.strip().isdigit():
            val = int(meta_page.strip())
            if val > 0:
                page_num = val
                page_str = f"p. {page_num}"

        # 2. Check evidence.page_info if page_num still not determined
        if page_num is None and evidence.page_info:
            raw_p = evidence.page_info.strip()
            # Match "p. 3", "Page 3", "pages 3-4", etc.
            match = re.search(r"\b(?:p\.|page|pages)?\s*(\d+)\b", raw_p, re.IGNORECASE)
            if match:
                parsed_val = int(match.group(1))
                if parsed_val > 0:
                    page_num = parsed_val
                    page_str = f"p. {page_num}"
            elif raw_p and raw_p != "p. N/A" and "n/a" not in raw_p.lower():
                page_str = raw_p

        # Extract section
        section = "N/A"
        raw_section = (
            evidence.section_path
            or evidence.metadata.get("section_title")
            or evidence.metadata.get("section_path")
        )
        if raw_section and str(raw_section).strip() and str(raw_section).strip().upper() != "N/A":
            section = str(raw_section).strip()

        # Build clean source label
        # e.g. "Academic Calendar 2026-27 — p. 3"
        base_title = doc_name.replace(".pdf", "").replace(".txt", "")
        base_title = re.sub(r"(\d)_(\d)", r"\1-\2", base_title)
        clean_doc_title = base_title.replace("_", " ")

        if page_num is not None:
            source_label = f"{clean_doc_title} — p. {page_num}"
        else:
            source_label = f"{clean_doc_title} — p. N/A"

        return {
            "document_id": doc_id,
            "document_name": doc_name,
            "page": page_num,
            "page_info": page_str,
            "section": section,
            "source": source_label,
            "chunk_id": evidence.chunk_id,
        }

    def _create_citation_item(
        self,
        citation_id: str,
        evidence: RetrievedEvidence,
        claim_text: str | None,
    ) -> CitationItem:
        """Create a validated CitationItem preserving genuine provenance."""
        prov = self.extract_provenance(evidence)
        return CitationItem(
            citation_id=citation_id,
            document_id=prov["document_id"],
            document_name=prov["document_name"],
            page=prov["page"],
            page_info=prov["page_info"],
            section=prov["section"],
            chunk_id=prov["chunk_id"],
            source=prov["source"],
            claim_text=claim_text,
            support_score=None,
            is_verified=False,
            metadata=dict(evidence.metadata),
        )

    def _compute_claim_evidence_match(self, claim: ClaimItem, evidence: RetrievedEvidence) -> float:
        """Compute matching support score between claim and evidence chunk in [0.0, 1.0]."""
        claim_text = claim.claim_text
        ev_text = evidence.text

        # 1. Exact entity containment check
        claim_entities = AcademicEntityExtractor.extract_entities(claim_text)
        ev_entities = AcademicEntityExtractor.extract_entities(ev_text)

        ev_entity_norms = {e.normalized_entity for e in ev_entities}
        claim_entity_norms = {e.normalized_entity for e in claim_entities}

        if claim_entity_norms:
            missing_entities = claim_entity_norms - ev_entity_norms
            if missing_entities:
                # If claim has critical academic entities (course code, specific date, regulation)
                # and evidence chunk doesn't contain them, this chunk cannot be the sole citation!
                return 0.0

        # 2. Token overlap of substantive words
        claim_tokens = self._extract_substantive_tokens(claim_text)
        ev_tokens = self._extract_substantive_tokens(ev_text)

        if not claim_tokens:
            return 0.0

        overlap = len(claim_tokens & ev_tokens) / len(claim_tokens)
        if overlap == 0.0:
            return 0.0

        # 3. Numeric / percentage check
        claim_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", claim_text))
        ev_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", ev_text))
        if claim_numbers:
            missing_nums = claim_numbers - ev_numbers
            if missing_nums:
                return 0.0

        # 4. Entity coverage
        if claim_entity_norms:
            entity_score = len(claim_entity_norms & ev_entity_norms) / len(claim_entity_norms)
        else:
            entity_score = overlap

        final_score = 0.5 * overlap + 0.5 * entity_score
        return min(1.0, max(0.0, final_score))

    def _extract_substantive_tokens(self, text: str) -> set[str]:
        """Extract normalized substantive alphanumeric content tokens."""
        raw_words = re.findall(r"[A-Za-z0-9]+(?:-[A-Za-z0-9]+)?", text.lower())
        return {w for w in raw_words if len(w) >= 2 and w not in self.STOPWORDS}
