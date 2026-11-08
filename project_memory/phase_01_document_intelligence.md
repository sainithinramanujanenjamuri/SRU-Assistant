# Phase 01 — Document Intelligence

## Status

COMPLETED

## Objective

Build the document intelligence layer for **SRU Assistant** that transforms raw academic documents (PDF, DOCX, TXT) into clean, structured, metadata-rich intermediate representations suitable for Phase 2 chunking and knowledge preparation.

## Scope

- Common document loader abstraction (`BaseDocumentLoader`) and loader factory.
- Format-specific document loaders for PDF (`PDFLoader`), Microsoft Word (`DOCXLoader`), and plain text (`TXTLoader`).
- Full-content SHA-256 canonical document identity (`document_id`).
- Preservation of unaltered raw extraction text and raw element stream.
- Unbroken provenance tracking (`document_id`, `source_file`, `page_number`, `line_number`, `structural_index`).
- Grid-preserving table extraction (rows, columns, headers, markdown representation).
- Text cleaning, Unicode normalization (NFKC), and conservative header/footer filtering that protects academic entities.
- Modular rule-based academic structure detectors (course codes, regulations, departments, semesters, academic years, exams, dates, categories).
- Strict evidence-based metadata extraction adhering to the Non-Fabrication principle.
- End-to-end processing pipeline with failure isolation for batch directory execution.
- Deterministic synthetic test fixtures and comprehensive unit and integration test suite.
- Command-line validation tooling for `documents/raw/`.

## Architecture

```text
documents/raw/
      │
      ▼
1. Validation & Hash (Full-content SHA-256 -> document_id)
      │
      ▼
2. Document Loader (PDFLoader / DOCXLoader / TXTLoader)
      │
      ▼
3. ExtractedDocument (Raw text & original DocumentElements preserved)
      │
      ▼
4. DocumentCleaner (NFKC norm, whitespace normalization, conservative header/footer filter)
      │
      ▼
5. StructureDetector (Modular detectors: Course, Regulation, Dept, Sem, Year, Exam, Date, Category)
      │
      ▼
6. MetadataExtractor (Evidence-based metadata assignment, no fabrication)
      │
      ▼
7. ProcessedDocument (Clean elements + tables + raw copy + metadata + academic entities)
      │
      ▼
documents/processed/<document_id>.json
```

## Implementation

- **Data Models (`ingestion/models.py`)**: Defined `ElementType` (StrEnum), `ElementProvenance`, `TableData`, `DocumentElement`, `ExtractedDocument`, `DocumentMetadata`, `DetectedAcademicStructures`, and `ProcessedDocument` with JSON serialization.
- **Loader Abstractions & Hash (`ingestion/loaders/base.py`)**: `BaseDocumentLoader` with custom exception hierarchy (`DocumentLoadingError`, `UnsupportedDocumentError`, `CorruptedDocumentError`, `EmptyDocumentError`) and `compute_file_sha256(path)` computing SHA-256 over entire source bytes.
- **Format Loaders (`ingestion/loaders/`)**:
  - `PDFLoader`: Page-by-page extraction via `pypdf.PdfReader`, assigning 1-indexed page numbers in provenance.
  - `DOCXLoader`: Document-order traversal of paragraphs, headings, and tables via `python-docx`. Preserves structured grid `TableData` and markdown tables.
  - `TXTLoader`: Plain-text loader with fallback encodings (`utf-8`, `utf-8-sig`, `latin-1`) and 1-indexed line numbers.
  - `DocumentLoaderFactory` / `get_loader_for_file`: Registry resolving loaders by file extension.
- **Cleaning & Normalization (`ingestion/processors/cleaner.py`)**: `DocumentCleaner` performs NFKC Unicode normalization, control character stripping (without gluing adjacent words), whitespace collapsing, and conservative header/footer filtering that protects academic lines matching regulations, course codes, exams, and dates.
- **Modular Structure Detectors (`ingestion/processors/detectors/`)**:
  - `CourseCodeDetector`: Detects course codes (e.g. `23CSE302T`, `20EC201`, `CS301`) with false-positive filtering.
  - `RegulationDetector`: Detects academic regulations (e.g. `R23`, `R20`).
  - `DepartmentDetector`: Detects department names and acronyms (e.g. `Computer Science and Engineering`, `ECE`, `MECH`).
  - `SemesterDetector`: Detects academic semesters (e.g. `Semester VII`, `Semester I`, `Odd Semester`).
  - `AcademicYearDetector`: Detects academic years (e.g. `2026-27`, `2025-2026`).
  - `ExaminationDetector`: Detects exam types (e.g. `Mid-Semester Examination I`, `End Semester Examinations`).
  - `DateDetector`: Detects single dates and date ranges (e.g. `12 September 2026 to 16 September 2026`).
  - `DocumentCategoryDetector`: Classifies document into `syllabus`, `academic_calendar`, `exam_schedule`, `exam_guidelines`, `department_notice`.
  - `StructureDetector`: Composite detector aggregating all modular detectors.
- **Metadata Extraction (`ingestion/metadata/extractor.py`)**: Strictly evidence-based `MetadataExtractor`. Does not guess or fabricate missing academic fields (leaves them as `None`).
- **Processing Pipeline (`ingestion/pipeline.py`)**: `DocumentPipeline` coordinating `process_file` and `process_directory` with batch failure isolation.
- **Validation Script (`scripts/validate_documents.py`)**: CLI runner for document processing on `documents/raw/`.

## Files Added

- `ingestion/models.py`
- `ingestion/loaders/base.py`
- `ingestion/loaders/pdf_loader.py`
- `ingestion/loaders/docx_loader.py`
- `ingestion/loaders/txt_loader.py`
- `ingestion/loaders/factory.py`
- `ingestion/processors/cleaner.py`
- `ingestion/processors/detectors/base.py`
- `ingestion/processors/detectors/course_code.py`
- `ingestion/processors/detectors/regulation.py`
- `ingestion/processors/detectors/department.py`
- `ingestion/processors/detectors/semester.py`
- `ingestion/processors/detectors/academic_year.py`
- `ingestion/processors/detectors/examination.py`
- `ingestion/processors/detectors/date_detector.py`
- `ingestion/processors/detectors/category.py`
- `ingestion/processors/detectors/__init__.py`
- `ingestion/processors/structure_detector.py`
- `ingestion/metadata/extractor.py`
- `ingestion/pipeline.py`
- `scripts/validate_documents.py`
- `tests/fixtures/fixture_generator.py`
- `tests/fixtures/__init__.py`
- `tests/ingestion/test_content_identity.py`
- `tests/ingestion/test_loaders.py`
- `tests/ingestion/test_provenance.py`
- `tests/ingestion/test_cleaners.py`
- `tests/ingestion/test_structure_detector.py`
- `tests/ingestion/test_metadata.py`
- `tests/integration/test_pipeline.py`
- `project_memory/phase_01_document_intelligence.md`

## Files Modified

- `pyproject.toml` (added `pypdf>=4.0.0`, `python-docx>=1.1.0`)
- `requirements.txt` (added `pypdf>=4.0.0`, `python-docx>=1.1.0`)
- `app/config/settings.py` (added ingestion configuration options)
- `ingestion/__init__.py` (exported ingestion components)
- `ingestion/loaders/__init__.py` (exported loaders and errors)
- `ingestion/processors/__init__.py` (exported cleaner and structure detector)
- `ingestion/metadata/__init__.py` (exported metadata extractor)
- `project_memory/README.md` (updated phase status table)

## Dependencies Added

- `pypdf>=4.0.0` (installed `pypdf 6.18.1`)
- `python-docx>=1.1.0` (installed `python-docx 1.2.0`, `lxml 6.1.3`)

## Data Model

The intermediate document representation `ProcessedDocument` contains:
- `document_id`: Deterministic 64-char hex SHA-256 digest of complete file content.
- `metadata`: `DocumentMetadata` containing non-fabricated academic and system attributes.
- `elements`: `list[DocumentElement]` containing cleaned and normalized elements with preserved provenance (`ElementProvenance`).
- `raw_elements_count`: Count of initial elements prior to cleaning.
- `raw_text`: Preserved copy of original extracted raw text for auditability.
- `cleaned_text`: Complete normalized text.
- `academic_structures`: `DetectedAcademicStructures` (course codes, regulations, departments, semesters, academic years, exams, dates, headings).

## Processing Pipeline

- `DocumentPipeline.process_file(file_path)`: Executes end-to-end extraction, cleaning, detection, and metadata extraction.
- `DocumentPipeline.process_directory(input_dir, output_dir)`: Scans supported extensions, processes files with error isolation, saves formatted JSON to `output_dir/<document_id>.json`, and returns an `IngestionBatchResult`.

## Tests

### Pytest Execution (Verbose)
Command:
```powershell
python -m pytest tests -v
```

Result:
```text
============================= test session starts =============================
platform win32 -- Python 3.11.9, pytest-9.0.2, pluggy-1.6.0
rootdir: D:\CapProject
configfile: pyproject.toml
plugins: anyio-3.7.1, asyncio-1.4.0, cov-7.1.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 34 items

tests\ingestion\test_cleaners.py ....                                    [ 11%]
tests\ingestion\test_content_identity.py ...                             [ 20%]
tests\ingestion\test_loaders.py .......                                  [ 41%]
tests\ingestion\test_metadata.py ..                                      [ 47%]
tests\ingestion\test_provenance.py ...                                   [ 55%]
tests\ingestion\test_structure_detector.py .........                     [ 82%]
tests\integration\test_pipeline.py ..                                    [ 88%]
tests\test_foundation.py ....                                            [100%]

============================= 34 passed in 0.85s ==============================
```

### Pytest Execution (Quiet)
Command:
```powershell
python -m pytest -q
```

Result:
```text
..................................                                       [100%]
34 passed in 0.85s
```

All 34 tests passed:
- `test_content_identity`: Identical content produces identical hash; different content produces different hash; filename renaming does not alter identity.
- `test_loaders`: PDF, DOCX (with tables), TXT loading; empty file handling; corrupted file handling; unsupported extensions; raw extraction preservation.
- `test_provenance`: PDF page provenance; TXT line provenance; DOCX table and structural provenance survival through cleaning.
- `test_cleaners`: Unicode normalization; whitespace collapsing; boilerplate header removal; protection of academic entities in headers.
- `test_structure_detector`: Independent modular detector unit tests (course codes, regulations, departments, semesters, academic years, exams, dates, categories, headings).
- `test_metadata`: Evidence-based extraction; strict non-fabrication rule enforcement.
- `test_pipeline`: Single-file processing and JSON roundtrip; batch directory processing with failure isolation.
- `test_foundation`: Core package imports, settings instantiation, directory layout, and RYU AI isolation.

## Validation

1. **Linter Check**:
   Command: `python -m ruff check .`
   Result: `All checks passed!`
2. **Directory Validation Script**:
   Command: `python scripts/validate_documents.py`
   Result:
   ```text
   ======================================================================
   SRU ASSISTANT -- PHASE 1 DOCUMENT INTELLIGENCE VALIDATION
   ======================================================================
   Raw Documents Directory      : D:\CapProject\documents\raw
   Processed Output Directory   : D:\CapProject\documents\processed
   Supported File Formats       : .pdf, .docx, .txt
   Candidate Files Found        : 0
   ----------------------------------------------------------------------
   Official SR University document validation: PENDING
   Reason: No official academic documents (.pdf, .docx, .txt) found in documents/raw/.
   Note: Automated unit and integration tests use deterministic test fixtures.
   ======================================================================
   ```
3. **Secret Scanning**:
   Scanned repository for tokens, API keys, and credentials. Result: `None`.
4. **RYU AI Isolation**:
   Scanned repository for RYU AI terminology and imports. Result: `None`.
5. **Specification Integrity**:
   Verified byte counts of `framework.md` (23551), `RAG.md` (34509), `roadmap.md` (26907), `agent.md` (46214) remain completely unchanged.
6. **Source Immutability**:
   Raw documents are opened strictly in read-only mode (`open("rb")`, `read_text()`); original source files are never altered.

## Real-Document Validation Status

**Official SR University document validation: PENDING**
- Reason: No official university documents are currently placed in `documents/raw/`.
- The pipeline, validation script, and loaders are fully configured and ready to process official documents as soon as they are added to `documents/raw/`.
- All automated testing was performed using deterministic synthetic fixtures.

## Problems Encountered

1. Word gluing in `normalize_text`: Unprintable control characters (`\x00-\x08`) without adjacent whitespace caused words to glue together (`AcademicCalendar`).
2. Script execution `sys.path`: Running `python scripts/validate_documents.py` directly from shell failed to resolve `app` because project root was not automatically in `sys.path`.

## Solutions

1. Updated `DocumentCleaner.normalize_text` to replace consecutive control characters with a space, allowing subsequent whitespace normalization to collapse spaces without gluing tokens.
2. Added `sys.path.insert(0, str(Path(__file__).resolve().parent.parent))` in `scripts/validate_documents.py` for resilient standalone CLI execution.

## Architectural Decisions

- **Full-Content SHA-256 for Identity**: Guaranteed content-addressable identity (`document_id`) independent of file path or naming variations.
- **Preservation of Raw Extraction**: Kept unaltered raw element streams and raw text on `ExtractedDocument` and `ProcessedDocument`, ensuring an audit trail for downstream citation and provenance.
- **Table Preservation via Structured Grid**: Retained `TableData` containing explicit row/column arrays alongside formatted markdown.
- **Modular Detector Hierarchy**: Replaced monolithic regex with single-responsibility detector classes aggregated by `StructureDetector`.
- **Conservative Header/Footer Filtering**: Prevented accidental deletion of academic headers by validating that repeated lines do not match course codes, regulations, or dates.
- **Evidence-Based Metadata (Non-Fabrication)**: Explicitly rejected guessing or inferring university metadata.

## Known Limitations

- Real university document validation is pending the placement of official SR University documents into `documents/raw/`.
- OCR for scanned images/non-text PDFs is not included (requires Tesseract/external OCR if needed in future research phases).
- Chunking, embeddings, vector stores, and LLMs are intentionally omitted (designated for Phase 2+).

## Remaining Work

None for Phase 1. Ready for Phase 2.

## Phase 2 Dependencies

- Intermediate `ProcessedDocument` representation (`documents/processed/<document_id>.json`).
- Element provenance (`ElementProvenance`) and structured tables (`TableData`).
- Detected academic entities (`DetectedAcademicStructures`).

## Final Phase Result

Phase 1 — Document Intelligence is **COMPLETED**.
All loaders, cleaners, detectors, metadata extractors, pipelines, test suites, and validation scripts are implemented, verified, and documented.
