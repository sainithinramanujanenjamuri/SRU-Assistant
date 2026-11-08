# Phase 8 — Citation & Provenance: Completion Report

**Project**: SRU Assistant: A RAG Framework for University Academic Query Resolution  
**Phase**: Phase 8 — Citation & Provenance  
**Status**: COMPLETE & VERIFIED  
**Date**: 2026-09-17  

---

## 1. Objective

Phase 8 established the complete **Citation & Provenance** layer for the SRU Assistant framework in strict compliance with `roadmap.md` (lines 659–723), `agent.md` (lines 471–496), `RAG.md` (lines 790–848), and `framework.md` (lines 452–500).

The primary objective is to make **every grounded answer traceable** through an unbroken provenance chain connecting physical documents to synthesized answers:
$$\text{Document} \longrightarrow \text{Page} \longrightarrow \text{Section} \longrightarrow \text{Chunk} \longrightarrow \text{Retrieved Evidence} \longrightarrow \text{Generated Claim} \longrightarrow \text{Citation}$$

---

## 2. Architecture

```text
User Academic Query
        ↓
Candidate Retrieval (EnhancedRetriever / HybridRetriever)
        ↓
ContextBuilder (Relevance Threshold & Token Budget Filtering)
        ↓
ConflictDetector (Cross-Document Contradiction Analysis)
        ↓
Grounded Generator (Deterministic Baseline or Neural LLM)
        ↓
GroundingValidator (Entity Containment & Faithfulness Audit)
        ↓
ClaimExtractor (Proposition Decomposition & Abbreviation Protection)
        ↓
CitationMapper (Claim-Evidence Alignment & Provenance Tracking)
        ↓
CitationVerifier (Deterministic Factual Audit & Precision/Recall Scoring)
        ↓
CitationFormatter (inline_bracket, source_block, footnote Rendering)
        ↓
RAGResponse (Cited Answer + Structured Citations + Verification Report + Telemetry)
```

---

## 3. Core Data Models (`citations/models.py`)

1. **`CitationItem`** (Frozen/Immutable):
   - `citation_id: str`: Sequential numeric string (e.g. `'1'`, `'2'`).
   - `document_id: str`: Canonical document SHA-256 identifier.
   - `document_name: str`: Human-readable filename (e.g. `'Academic_Calendar_2026_27.pdf'`).
   - `page: int | None`: 1-indexed integer page number or `None`.
   - `page_info: str`: Formatted page string (e.g. `'p. 3'` or `'p. N/A'`).
   - `section: str`: Hierarchical section title or breadcrumb.
   - `chunk_id: str`: Originating chunk identifier.
   - `source: str`: Human-readable citation label (e.g. `'Academic Calendar 2026-27 — p. 3'`).
   - `claim_text: str | None`: Atomic claim supported by this citation.
   - `support_score: float | None`: Support confidence score in $[0.0, 1.0]$.
   - `is_verified: bool`: Verification audit outcome.
   - `metadata: dict[str, Any]`: Retained chunk provenance metadata.

2. **`ClaimItem`** (Frozen/Immutable):
   - `claim_id: str`: Stable sequential identifier (`'claim_1'`, `'claim_2'`).
   - `claim_text: str`: Cleaned factual proposition.
   - `claim_type: Literal["factual", "date", "policy", "general"]`: Domain classification.
   - `associated_citation_ids: list[str]`: Ordered citation IDs linked to this claim.
   - `is_supported: bool`: Substantive support flag.
   - `support_evidence_chunk_ids: list[str]`: Backing chunk IDs.
   - `support_score: float`: Factual match score in $[0.0, 1.0]$.
   - `entities: list[str]`: University academic entities contained in the claim.

3. **`CitationVerificationResult`** (Frozen/Immutable):
   - `is_fully_supported: bool`: True if all claims are verified without ungrounded assertions.
   - `overall_support_score: float`: Mean support score across claims in $[0.0, 1.0]$.
   - `citation_precision: float`: Verified citations / total emitted citations.
   - `citation_recall: float`: Supported claims / total extractable factual claims.
   - `claims: list[ClaimItem]`: Detailed claim audit list.
   - `citations: list[CitationItem]`: Detailed citation audit list.
   - `unsupported_claims: list[str]`: Text of unverified or unsupported claims.
   - `unverified_citations: list[str]`: Citation IDs failing verification.
   - `verification_latency_ms: float`: Measurement in milliseconds.

---

## 4. Claim Extraction Subsystem (`citations/claim_extractor.py`)

- **Proposition Decomposition**: Tokenizes answers into discrete factual assertions while protecting institutional abbreviations (`Dr.`, `Prof.`, `B.Tech.`, `M.Tech.`, `Ph.D.`, `p.`, `No.`, etc.) using temporary sentinel tokenization.
- **Rhetorical & Conversational Stripping**: Strips meta-framing prefixes (`"Based on the provided documents,"`, `"According to the official regulations,"`) and discards introductory preamble headers ending with colons (`:`).
- **Domain Entity Extraction**: Leverages `AcademicEntityExtractor` to detect course codes (`23CSE302T`), calendar dates (`12 September 2026`), examination types (`Mid-Semester Examination I`), and regulations (`R23`).
- **Claim Classification**: Classifies statements into `date`, `policy`, `factual`, or `general`.

---

## 5. Citation Mapping Subsystem (`citations/citation_mapper.py`)

- **Claim-to-Evidence Alignment**: Matches claims against retrieved evidence chunks actually supplied to generation using entity containment, exact numeric/percentage matching, and substantive token overlap.
- **Citation ID Allocation**: Assigns stable, sequential citation identifiers (`1`, `2`, `3`).
- **Source Reuse**: If the same evidence chunk supports multiple distinct claims, the same citation ID and `CitationItem` are reused rather than creating redundant duplicates.
- **Multi-Document Support**: Seamlessly maps multi-part answers to distinct documents (e.g. syllabus objectives to citation `[1]` and exam calendar dates to citation `[2]`).

---

## 6. Citation Verification Subsystem (`citations/citation_verifier.py`)

- **Factual Audit ("Claim ≠ Entity")**: Specifically guards against false verification where an entity appears in evidence without supporting the predicate claim. If an exam date claim mentions course code `23CSE302T`, but evidence only contains course description without exam schedule, the claim is flagged as unsupported.
- **Exact Numeric & Entity Containment**: Enforces that course codes, dates, percentages (e.g. `75%`), and credit figures must be present in cited evidence.
- **Operational Metrics**:
  - $\text{Citation Precision} = \frac{\text{Verified Citations}}{\text{Total Emitted Citations}}$
  - $\text{Citation Recall} = \frac{\text{Supported Claims}}{\text{Total Factual Claims}}$
  - $\text{Overall Support Score} = \frac{1}{M} \sum_{c \in \text{claims}} c.\text{support\_score}$
- **Unsupported Claim Handling**: Unsupported claims are retained in `unsupported_claims` with `is_supported = False` and are NOT falsely assigned nearest citations.

---

## 7. Provenance Preservation & Zero-Fabrication Rule

- In strict compliance with `agent.md` line 494 ("Do not generate fake page numbers, sections, or source names"):
  - Valid page numbers are parsed directly from `page_info` or metadata (e.g. `"p. 3"` $\to$ `3`).
  - Missing page numbers are explicitly preserved as `page = None` and `page_info = "p. N/A"`.
  - Sections are extracted directly from `section_path` or document structure metadata; missing sections output `"N/A"`.
  - Document names and chunk IDs are directly preserved from retrieved evidence.
  - The system **never** infers page numbers from chunk indices, rank order, or array positions.

---

## 8. Citation Rendering Subsystem (`citations/formatter.py`)

Provides three canonical citation styles:
1. **`inline_bracket`**:
   ```text
   The mid-semester examinations are scheduled for 12–16 September 2026. [1]

   Sources:
   [1] Academic Calendar 2026-27 — p. 3
       Section: Academic Calendar 2026-27 > Examination Schedule
   ```
2. **`source_block`**:
   ```text
   The mid-semester examinations are scheduled for 12–16 September 2026.

   Source:
   - Academic Calendar 2026-27 — p. 3
     Section: Academic Calendar 2026-27 > Examination Schedule
   ```
3. **`footnote`**:
   ```text
   The mid-semester examinations are scheduled for 12–16 September 2026.¹

   Footnotes:
   ¹ Academic Calendar 2026-27 — p. 3 (Section: Examination Schedule)
   ```

---

## 9. Pipeline Integration (`generation/pipeline.py`)

- Extended `BaselineRAGPipeline.answer_query` with Step 9 (Citation Processing):
  - Extracts claims $\to$ Maps evidence $\to$ Verifies citations $\to$ Formats cited answer.
- Respects safe no-answer short-circuiting: on insufficient evidence, citations list is empty (`citations = []`, `citation_verification = None`, `citation_latency_ms = 0.0`), preventing any hallucinated citations.
- Extended `RAGResponse` with:
  - `citations: list[CitationItem]`
  - `citation_verification: CitationVerificationResult | None`
  - `citation_latency_ms: float`
  - `cited_answer: str | None`

---

## 10. Configuration Settings (`app/config/settings.py` & `.env.example`)

- `citation_style`: `"inline_bracket"` (allowed: `"inline_bracket"`, `"source_block"`, `"footnote"`).
- `citation_verification_enabled`: `True` (boolean).
- `citation_min_support_score`: `0.50` (float in $[0.0, 1.0]$).
- `citation_require_exact_entities`: `True` (boolean).

---

## 11. Test Results & Verification

### Test Suite Execution
- **Command**: `pytest tests/citations/ tests/integration/test_rag_citations.py -v`
- **Results**: **35 passed in 0.55s**
  - `tests/citations/test_models.py`: 7 passed
  - `tests/citations/test_claim_extractor.py`: 6 passed
  - `tests/citations/test_citation_mapper.py`: 6 passed
  - `tests/citations/test_citation_verifier.py`: 5 passed
  - `tests/citations/test_formatter.py`: 6 passed
  - `tests/integration/test_rag_citations.py`: 5 passed
- **Full Regression Suite**: `pytest tests -q`
  - **261 passed in 16.48s** (zero regressions across all phases).
- **Static Analysis**: `ruff check .`
  - **All checks passed** (0 errors, 0 warnings).

---

## 12. Empirical Citation Benchmark

- **Harness**: `scripts/evaluate_citations.py`
- **Output Artifact**: `data/benchmarks/citation_benchmark.json`
- **Dataset Hash**: `2c6ea6912dd4deff4eaee14c42ff09d45909848964417374492f18dd6d8be15f`
- **Evaluation Categories**:
  1. `single_document_factual`: Single-source exam schedule.
  2. `multi_document_synthesis`: Multi-source syllabus + calendar queries.
  3. `insufficient_evidence`: Out-of-domain unanswerable queries.
  4. `unsupported_claims`: Adversarial ungrounded assertions.
  5. `provenance_edge_cases`: Missing page/section metadata handling.

### Benchmark Metrics Achieved
| Metric | Value | Target | Status |
|---|---|---|---|
| Macro Citation Precision | **100.00%** | > 90% | EXCEEDED |
| Macro Citation Recall | **90.00%** | > 85% | EXCEEDED |
| Average Support Score | **0.9000** | > 0.80 | EXCEEDED |
| Provenance Integrity Rate | **100.00%** | 100% | MET (Zero fake pages/sections) |

### Latency Profile (5 repetitions per query)
| Component | Mean | Median | P95 |
|---|---|---|---|
| Claim Extraction | 0.163 ms | 0.131 ms | 0.280 ms |
| Citation Mapping | 0.131 ms | 0.113 ms | 0.245 ms |
| Citation Verification | 0.151 ms | 0.148 ms | 0.210 ms |
| Citation Formatting | 0.031 ms | 0.011 ms | 0.090 ms |
| **Total Citation Processing** | **0.476 ms** | **0.450 ms** | **1.107 ms** |

---

## 13. Manual CLI Verification Evidence

1. **`--citation-style inline_bracket`**:
   - Query: `"When are the mid-semester examinations scheduled?"`
   - Output: In-text `[1]` markers appended to Mid-I and Mid-II dates; `Sources:` bibliography printed at bottom.
   - Status: Verified.
2. **`--citation-style source_block`**:
   - Query: `"When are the mid-semester examinations scheduled?"`
   - Output: Clean answer body with structured `Source:` block appended.
   - Status: Verified.
3. **`--citation-style footnote`**:
   - Query: `"When are the mid-semester examinations scheduled?"`
   - Output: Superscript numerals (`¹`) with `Footnotes:` list.
   - Status: Verified.
4. **Out-of-Scope Query (Zero False Citations)**:
   - Query: `"What is the capital of Australia?"`
   - Output: Fallback text emitted, `CITATIONS (0 emitted): [No citations emitted]`, `citation_latency_ms: 0.0 ms`.
   - Status: Verified.
5. **`--no-verify-citations`**:
   - Status: Verified (verification audit skipped, citations emitted with status `UNVERIFIED`).

---

## 14. Failures & Engineering Fixes

1. **Circular Import During Package Loading**:
   - *Failure*: `generation.models` importing `citations.models` triggered `citations/__init__.py`, which imported `CitationMapper`, which imported `AcademicEntityExtractor`, which imported `generation.grounding.__init__`, which imported `ConflictDetector`, which imported partially initialized `generation.models`.
   - *Fix*: Implemented PEP 562 `__getattr__` lazy attribute loading in `citations/__init__.py`. Direct imports of `citations.models` load in complete isolation with zero circular dependencies.
2. **Abbreviation False Splitting**:
   - *Failure*: Sentence regex split on `Prof.` and `B.Tech.` when periods were followed by capitalized words.
   - *Fix*: Masked protected abbreviations with sentinel tokens (`__ABBR_{idx}__`) prior to sentence splitting, restoring periods afterward.
3. **Preamble Header Claim Extraction**:
   - *Failure*: Introductory preamble lines like `"Based on the official SR University documentation:"` were extracted as candidate claims and failed verification.
   - *Fix*: Added pattern filters to discard colon-terminated header lines and documentation intro sentences.
4. **Zero-Overlap False Citation Mapping**:
   - *Failure*: In queries with no academic entities, fallback entity coverage returned `1.0`, resulting in a composite score of `0.50` exceeding the `0.40` threshold.
   - *Fix*: Hard gate requiring `overlap > 0.0` before computing composite scores.

---

## 15. Architectural Decisions

1. **Deterministic Operational Metrics**: Rather than relying on non-deterministic LLM-as-a-judge for citation verification in CI, Phase 8 establishes deterministic entity containment, token overlap, and predicate co-occurrence metrics.
2. **Immutable Frozen Models**: `CitationItem`, `ClaimItem`, and `CitationVerificationResult` are frozen Pydantic models preventing inadvertent state mutations.
3. **Strict Provenance Integrity**: The system explicitly forbids inferring or synthesizing missing page numbers from chunk indices or rank ordering. Missing metadata is rendered as `"p. N/A"` or omitted cleanly.

---

## 16. Canonical Specification Integrity

Byte counts and SHA-256 integrity checks confirmed that all canonical specification files remain 100% untouched:
- `framework.md`: 23,551 bytes
- `RAG.md`: 34,509 bytes
- `roadmap.md`: 26,907 bytes
- `agent.md`: 46,214 bytes

---

## 17. RYU AI Independence Audit

A comprehensive search across the repository confirmed **zero imports, zero dependencies, and zero references to RYU AI** in the Phase 8 implementation.

---

## 18. Known Limitations & Phase 9 Dependencies

- **Interactive UI**: Phase 8 provides textual formatting for CLI and API responses (`[1]`, `¹`). Interactive clickable citation popups and document page viewers are reserved for **Phase 10 — Application Layer**.
- **Automated RAG Triad Evaluation**: Phase 8 evaluates operational citation metrics (precision, recall, support score). End-to-end automated evaluation of context relevance, answer relevance, and faithfulness across an extensive 10-category benchmark suite is reserved for **Phase 9 — RAG Evaluation**.
