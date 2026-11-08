# SRU Assistant --- RAG Architecture Specification

## 1. Purpose

This document defines the Retrieval-Augmented Generation (RAG)
architecture for **SRU Assistant: A RAG Framework for University
Academic Query Resolution**.

SRU Assistant is a standalone project. It is completely separate from
the RYU AI Framework and does not use RYU-specific architecture,
terminology, runtime components, agents, workers, spaces, or
autonomous-system concepts.

The approved project describes a system that ingests SR University
academic documents, converts their content into vector embeddings,
stores them in a searchable vector database, retrieves relevant document
segments for a student's query, and uses a Large Language Model (LLM) to
generate a context-aware answer with citations to the source material.

------------------------------------------------------------------------

# 2. RAG Strategy

The project will use a **Hybrid, Source-Grounded RAG architecture**.

The architecture combines:

1.  Document ingestion
2.  Document processing
3.  Semantic/vector retrieval
4.  Lexical/keyword retrieval
5.  Metadata-aware filtering
6.  Candidate fusion
7.  Re-ranking
8.  Evidence construction
9.  LLM-based grounded generation
10. Citation and provenance tracking
11. Grounding validation
12. Retrieval and answer evaluation

The core principle is:

> **Retrieve first. Generate second. Cite the evidence.**

The LLM is not treated as the authoritative source for
university-specific information. Institutional documents are the
knowledge source.

------------------------------------------------------------------------

# 3. Why Hybrid RAG?

A university knowledge base contains different types of information.

Some questions depend primarily on semantic similarity:

> "When do my mid exams start?"

while others depend on exact lexical information:

> "What is 23CSE302T?"

or:

> "What is the attendance requirement under Regulation R23?"

A purely vector-based system may perform well for semantic questions but
can be weaker for exact identifiers, course codes, regulation numbers,
dates, names, and other precise terms.

Therefore, SRU Assistant will combine:

``` text
              User Query
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
 Semantic Retrieval    Lexical Retrieval
    Vector Search          BM25
        │                   │
        └─────────┬─────────┘
                  ▼
             Candidate
               Fusion
                  │
                  ▼
          Metadata Filtering
                  │
                  ▼
             Re-ranking
                  │
                  ▼
          Evidence Selection
                  │
                  ▼
                 LLM
                  │
                  ▼
          Grounded Answer
                  │
                  ▼
              Citations
```

------------------------------------------------------------------------

# 4. Complete RAG Pipeline

``` text
                 ┌──────────────────────────┐
                 │ Official SR University   │
                 │ Academic Documents       │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Document Ingestion       │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Extraction & Cleaning     │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Structure Detection       │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Chunking + Metadata       │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Embedding Generation     │
                 └────────────┬─────────────┘
                              │
                              ▼
                 ┌──────────────────────────┐
                 │ Vector Database           │
                 └────────────┬─────────────┘
                              │
                              │
 Student Query ───────────────┤
                              ▼
                 ┌──────────────────────────┐
                 │ Query Processing          │
                 └────────────┬─────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
             Vector Search          BM25 Search
                    │                   │
                    └─────────┬─────────┘
                              ▼
                    Candidate Fusion
                              │
                              ▼
                    Metadata Filtering
                              │
                              ▼
                       Re-ranker
                              │
                              ▼
                    Evidence Selection
                              │
                              ▼
                    Context Construction
                              │
                              ▼
                         LLM Layer
                              │
                              ▼
                   Grounding Validation
                              │
                              ▼
                    Citation Construction
                              │
                              ▼
                     Final Response
```

------------------------------------------------------------------------

# 5. Layer 1 --- Document Ingestion

## Objective

Convert institutional source documents into a normalized representation
suitable for retrieval.

Supported document types may include:

-   PDF
-   DOCX
-   TXT
-   Structured academic data
-   Department notices
-   Academic schedules
-   Course structures
-   Examination guidelines

The initial implementation should prioritize the document formats
actually available for the project.

------------------------------------------------------------------------

## Ingestion Flow

``` text
Raw Document
     ↓
File Validation
     ↓
Document Loader
     ↓
Text Extraction
     ↓
Cleaning
     ↓
Structure Detection
     ↓
Metadata Extraction
     ↓
Chunking
```

------------------------------------------------------------------------

# 6. Document Provenance

Every processed document should retain its origin.

Minimum conceptual provenance:

``` text
document_id
document_name
source
document_type
department
program
semester
academic_year
version
page_number
section
ingestion_timestamp
```

The exact metadata schema will be finalized during implementation.

Provenance is critical because the final answer must be traceable back
to the source material.

------------------------------------------------------------------------

# 7. Layer 2 --- Text Processing

Raw extracted text may contain:

-   Repeated headers
-   Footers
-   Page numbers
-   Broken line structures
-   Unnecessary whitespace
-   OCR artifacts
-   Table formatting problems

The processing layer should normalize the content without destroying
information needed for retrieval or citation.

Conceptual flow:

``` text
Extracted Text
     ↓
Normalization
     ↓
Noise Removal
     ↓
Structure Preservation
     ↓
Clean Document Representation
```

The processing pipeline should preserve:

-   Headings
-   Sections
-   Tables where possible
-   Page boundaries
-   Course codes
-   Dates
-   Names
-   Regulation identifiers
-   Other academically meaningful entities

------------------------------------------------------------------------

# 8. Layer 3 --- Chunking

Documents are divided into retrievable chunks.

The goal is not simply to create equally sized text blocks.

A good chunk should represent a coherent unit of information.

Example:

``` text
Document:
Academic Calendar 2026-27

Section:
Mid-Semester Examinations

Chunk:
Mid-Semester Examination-I:
12 September 2026 – 16 September 2026
```

Metadata remains attached to the chunk.

``` text
chunk_id
document_id
page_number
section
department
program
semester
academic_year
document_type
source
```

------------------------------------------------------------------------

# 9. Chunking Strategy

The initial system should use a practical baseline such as
structure-aware or recursive chunking.

Potential parameters:

``` text
chunk_size
chunk_overlap
separator hierarchy
minimum chunk size
maximum chunk size
```

These parameters should not be assumed to be optimal.

They should be evaluated experimentally.

Possible future strategies:

-   Recursive chunking
-   Heading-aware chunking
-   Parent-child chunks
-   Table-aware chunking
-   Semantic chunking

------------------------------------------------------------------------

# 10. Layer 4 --- Embedding Generation

Each chunk is converted into a vector representation.

``` text
Chunk Text
    ↓
Embedding Model
    ↓
Dense Vector
    ↓
Vector Index
```

The embedding model should support semantic similarity between:

-   Student questions
-   Academic terminology
-   Course information
-   Regulations
-   Schedules
-   University notices

The specific embedding model is an implementation decision and should be
benchmarked rather than assumed.

------------------------------------------------------------------------

# 11. Layer 5 --- Vector Database

The vector database stores the searchable knowledge representation.

Conceptually:

``` text
┌──────────────────────────────────────┐
│ Vector Database                      │
├──────────────────────────────────────┤
│ Embedding                            │
│ Chunk Text                           │
│ Chunk ID                             │
│ Document ID                          │
│ Metadata                             │
│ Provenance                           │
└──────────────────────────────────────┘
```

A retrieval operation should be capable of returning both:

``` text
Similarity Information
+
Source Metadata
```

This allows retrieval and citation to remain connected.

------------------------------------------------------------------------

# 12. Layer 6 --- Lexical Retrieval

SRU Assistant will include lexical retrieval alongside vector retrieval.

A BM25-style retriever can identify documents containing exact terms.

This is particularly useful for:

-   Course codes
-   Regulation numbers
-   Faculty names
-   Department names
-   Exact dates
-   Examination names
-   Technical abbreviations
-   Unique identifiers

Example:

``` text
Query:
"23CSE302T"

        ↓

Lexical Retrieval

        ↓

Documents containing:
"23CSE302T"
```

------------------------------------------------------------------------

# 13. Layer 7 --- Semantic Retrieval

The semantic retriever converts the query into an embedding and searches
for semantically similar chunks.

Example:

``` text
Query:
"When do my mid exams start?"

        ↓

Query Embedding

        ↓

Vector Search

        ↓

Relevant chunks:
"Mid-Semester Examination-I..."
```

This enables retrieval even when the query wording differs from the
wording in the source.

------------------------------------------------------------------------

# 14. Layer 8 --- Hybrid Candidate Fusion

The outputs from lexical and semantic retrieval are combined.

``` text
                 Query
                   │
          ┌────────┴────────┐
          ▼                 ▼
     Vector Search       BM25 Search
          │                 │
          ▼                 ▼
      Candidates         Candidates
          │                 │
          └────────┬────────┘
                   ▼
             Fusion Layer
                   │
                   ▼
          Unified Candidate Set
```

Possible fusion methods include:

-   Weighted score fusion
-   Reciprocal Rank Fusion (RRF)
-   Normalized score combination

The fusion strategy should be evaluated using the project's retrieval
dataset.

------------------------------------------------------------------------

# 15. Layer 9 --- Metadata Filtering

Metadata can constrain retrieval.

Example:

``` text
Query:
"VII semester CSE exam schedule"

Potential filters:

department = CSE
semester = VII
document_type = examination_schedule
```

Metadata filtering can reduce irrelevant retrieval candidates before or
after semantic/lexical search depending on the implementation.

The framework should avoid excessive filtering that could accidentally
remove the correct evidence.

------------------------------------------------------------------------

# 16. Layer 10 --- Re-ranking

Initial retrieval may return a relatively large candidate pool.

Example:

``` text
Vector + BM25
       ↓
100 candidates
       ↓
Re-ranker
       ↓
10 highly relevant candidates
```

A re-ranker evaluates the relationship between:

``` text
Query
+
Candidate Passage
```

rather than relying only on the independent vector similarity score.

The re-ranker should improve the quality of evidence presented to the
LLM.

------------------------------------------------------------------------

# 17. Retrieval Pipeline

The complete retrieval path becomes:

``` text
User Query
    ↓
Query Normalization
    ↓
Query Analysis
    ↓
 ┌───────────────────────┐
 │                       │
 ▼                       ▼
Dense Retrieval      BM25 Retrieval
 │                       │
 └───────────┬───────────┘
             ▼
       Candidate Fusion
             ↓
      Metadata Filtering
             ↓
         Re-ranking
             ↓
      Top-K Evidence
```

------------------------------------------------------------------------

# 18. Query Analysis

The query processing layer may identify useful characteristics such as:

``` text
department
program
semester
academic year
document type
course code
date
question type
```

Example:

``` text
"What is the CSE VII semester examination date?"

Detected:

department = CSE
semester = VII
question_type = date
document_type = examination-related
```

Query analysis should support retrieval; it should not unnecessarily
restrict queries.

------------------------------------------------------------------------

# 19. Adaptive Retrieval

A later version may use different retrieval behavior depending on query
type.

Example:

``` text
Course Code Query
      ↓
Lexical-heavy retrieval

Conceptual Question
      ↓
Semantic-heavy retrieval

Mixed Query
      ↓
Hybrid retrieval
```

This should only be implemented after baseline evaluation demonstrates
that adaptive retrieval provides measurable value.

------------------------------------------------------------------------

# 20. Layer 11 --- Evidence Selection

The final retrieval stage selects the evidence that will be passed to
the LLM.

The evidence package should contain:

``` text
Chunk Text
Document
Page
Section
Metadata
Relevance Information
Provenance
```

Example:

``` text
[Evidence 1]
Document: Academic Calendar 2026-27
Page: 3
Section: Examination Schedule

Content:
Mid-Semester Examination-I:
12 September 2026 – 16 September 2026
```

------------------------------------------------------------------------

# 21. Layer 12 --- Context Construction

The evidence is converted into a structured context for the LLM.

Conceptually:

``` text
SYSTEM INSTRUCTIONS

Use only the supplied university evidence
for university-specific factual claims.

EVIDENCE

[Source 1]
...

[Source 2]
...

USER QUERY

...
```

This makes the evidence boundary explicit.

------------------------------------------------------------------------

# 22. Layer 13 --- LLM Generation

The LLM receives:

``` text
User Query
+
Retrieved Evidence
+
Generation Instructions
```

Its responsibilities are:

-   Understand the question
-   Interpret retrieved evidence
-   Synthesize relevant information
-   Generate a natural-language answer
-   Avoid unsupported university-specific claims
-   Preserve exact academic information
-   Associate factual claims with sources

The model itself should not be considered the university knowledge base.

------------------------------------------------------------------------

# 23. Grounding Rules

## Rule 1 --- Evidence First

University-specific answers must be based on retrieved institutional
evidence.

## Rule 2 --- No Unsupported Facts

The model should not fabricate missing information.

## Rule 3 --- Insufficient Evidence

If the retrieved evidence is insufficient:

``` text
"I couldn't find sufficient information in the
available SR University documents to answer this accurately."
```

## Rule 4 --- Source Traceability

The response should identify the relevant source material.

## Rule 5 --- Conflict Awareness

If sources contain conflicting information, the system should surface
the conflict instead of silently producing a single unsupported
conclusion.

------------------------------------------------------------------------

# 24. Layer 14 --- Citation System

Citations are a first-class component of SRU Assistant.

The system should preserve:

``` text
Document
   ↓
Page
   ↓
Section
   ↓
Chunk
   ↓
Retrieved Evidence
   ↓
Generated Claim
   ↓
Citation
```

Possible final representation:

``` text
The first mid-semester examination is scheduled
from September 12 to September 16, 2026.

Source:
Academic Calendar 2026-27 — Page 3
```

The exact UI representation can later become clickable.

------------------------------------------------------------------------

# 25. Citation Verification

A future validation layer can evaluate whether a generated claim is
supported by its cited evidence.

Conceptual pipeline:

``` text
Generated Answer
       ↓
Claim Extraction
       ↓
Claim ↔ Evidence Matching
       ↓
Support Check
       ↓
Citation Validation
```

This can become one of the important research components of the project.

------------------------------------------------------------------------

# 26. Grounding Validation

Before returning the final response, the system may perform a grounding
check.

``` text
LLM Answer
    ↓
Grounding Validator
    ↓
 ┌───────────────┬─────────────────┐
 ▼               ▼
Supported      Unsupported
 ▼               ▼
Return         Revise / Reject
```

The first implementation should establish a reliable baseline before
introducing complex validation.

------------------------------------------------------------------------

# 27. No-Answer Handling

Not every question will have an answer in the knowledge base.

Example:

``` text
User:
"What is the university's policy on something
not contained in our indexed documents?"

             ↓

Retrieval

             ↓

Insufficient Evidence

             ↓

Controlled Response
```

The system should explicitly distinguish:

``` text
No answer found
```

from:

``` text
The answer is X
```

This is important for reducing hallucinated responses.

------------------------------------------------------------------------

# 28. Multi-Document Questions

Some queries may require information from multiple documents.

Example:

> "What subjects do I have this semester and when are their exams?"

Potential evidence:

``` text
Course Structure
       +
Examination Schedule
       ↓
   Evidence Set
       ↓
      LLM
       ↓
Combined Answer
       ↓
Multiple Citations
```

The framework should therefore support multiple retrieved sources per
response.

------------------------------------------------------------------------

# 29. Version-Aware Retrieval

Academic information changes over time.

Documents should therefore retain version-related metadata where
available:

``` text
academic_year
semester
publication_date
version
document_status
ingestion_timestamp
```

The retrieval system should avoid mixing information from different
academic periods when the query clearly refers to a particular period.

------------------------------------------------------------------------

# 30. RAG Knowledge Lifecycle

The knowledge base should be updateable.

``` text
New University Document
          ↓
Validation
          ↓
Ingestion
          ↓
Processing
          ↓
Chunking
          ↓
Embedding
          ↓
Index Update
          ↓
Available for Retrieval
```

Existing documents should not require application-code changes merely
because new academic documents are added.

------------------------------------------------------------------------

# 31. RAG Storage Model

A conceptual record:

``` json
{
  "chunk_id": "chunk_001",
  "document_id": "doc_2026_calendar",
  "text": "Mid-Semester Examination-I...",
  "embedding": "<vector>",
  "metadata": {
    "department": "CSE",
    "semester": "VII",
    "academic_year": "2026-27",
    "document_type": "academic_calendar",
    "page": 3
  },
  "provenance": {
    "source": "Academic Calendar 2026-27",
    "page": 3,
    "section": "Examination Schedule"
  }
}
```

This is a conceptual schema. The production schema will depend on the
selected vector database.

------------------------------------------------------------------------

# 32. Retrieval Quality Evaluation

Retrieval must be evaluated independently from generation.

Possible metrics:

### Recall@K

Measures whether relevant evidence appears within the top K retrieved
results.

### Precision@K

Measures how many retrieved results are relevant.

### MRR

Measures how highly the first relevant result appears.

### nDCG

Measures ranking quality when multiple results have different relevance
levels.

------------------------------------------------------------------------

# 33. Generation Evaluation

Generated answers can be evaluated on:

-   Correctness
-   Relevance
-   Completeness
-   Groundedness
-   Citation accuracy

A response should not be considered successful merely because it sounds
fluent.

The underlying evidence must support the answer.

------------------------------------------------------------------------

# 34. Hallucination / Unsupported Claim Evaluation

We should explicitly measure unsupported claims.

Conceptually:

``` text
Answer
 ↓
Claims
 ↓
Evidence Matching
 ↓
Supported Claims
+
Unsupported Claims
```

A useful metric can be:

``` text
Unsupported Claim Rate
=
Unsupported Claims / Total Factual Claims
```

The exact evaluation methodology should be finalized when the benchmark
dataset is created.

------------------------------------------------------------------------

# 35. End-to-End Evaluation

The complete evaluation pipeline:

``` text
Question Dataset
       ↓
SRU Assistant
       ↓
Retrieval Results
       ↓
Generated Answers
       ↓
Citations
       ↓
Evaluation
       │
       ├── Retrieval Metrics
       ├── Answer Metrics
       ├── Grounding Metrics
       ├── Citation Metrics
       └── Latency Metrics
```

------------------------------------------------------------------------

# 36. Baseline vs Enhanced RAG

The project should be developed experimentally.

## Baseline RAG

``` text
Documents
 ↓
Chunking
 ↓
Embeddings
 ↓
Vector Search
 ↓
LLM
 ↓
Citation
```

## Hybrid RAG

``` text
Documents
 ↓
Chunking
 ↓
Embeddings + BM25
 ↓
Hybrid Retrieval
 ↓
Metadata Filtering
 ↓
Re-ranking
 ↓
LLM
 ↓
Citation
```

## Enhanced RAG

Potential additions:

``` text
Query Rewriting
Adaptive Retrieval
Hybrid Search
Re-ranking
Context Compression
Multi-document Reasoning
Grounding Validation
Citation Verification
Version Awareness
```

The enhanced architecture should only include components that
demonstrate measurable benefit.

------------------------------------------------------------------------

# 37. Research Experimental Design

The framework should allow controlled comparison.

Example:

``` text
Experiment A
Vector RAG

        VS

Experiment B
Hybrid RAG

        VS

Experiment C
Hybrid + Re-ranking

        VS

Experiment D
Hybrid + Re-ranking + Grounding Validation
```

Compare them using the same evaluation dataset.

This makes the capstone more than a software demonstration: it becomes
an evaluated RAG framework.

------------------------------------------------------------------------

# 38. Query Benchmark Categories

The evaluation dataset should contain questions from multiple
categories.

``` text
1. Direct factual questions
2. Date-based questions
3. Course-related questions
4. Regulation questions
5. Department-specific questions
6. Multi-document questions
7. Paraphrased questions
8. Ambiguous questions
9. Out-of-knowledge-base questions
10. Version-sensitive questions
```

Each question should have ground-truth evidence where possible.

------------------------------------------------------------------------

# 39. Example End-to-End Query

### User Query

> "When is the CSE VII semester mid-semester examination?"

### Step 1 --- Query Analysis

``` text
department = CSE
semester = VII
question_type = schedule
```

### Step 2 --- Retrieval

``` text
Dense Search
+
BM25
```

### Step 3 --- Fusion

``` text
Candidate Pool
```

### Step 4 --- Metadata Filtering

``` text
CSE
VII Semester
Relevant Academic Year
```

### Step 5 --- Re-ranking

``` text
Top Relevant Chunks
```

### Step 6 --- Evidence

``` text
Academic Calendar
Page 3
Examination Schedule
```

### Step 7 --- LLM

Generate answer using the evidence.

### Step 8 --- Citation

Attach the source information.

### Final

``` text
The CSE VII semester mid-semester examination
is scheduled according to the retrieved academic
calendar.

Source:
Academic Calendar — Page 3
```

The actual answer must always come from the indexed university evidence.

------------------------------------------------------------------------

# 40. Error Boundaries

Failures should remain explicit.

``` text
Document Failure
      ↓
Ingestion Layer

Retrieval Failure
      ↓
Retrieval Layer

Evidence Failure
      ↓
Evidence Layer

Generation Failure
      ↓
LLM Layer

Citation Failure
      ↓
Citation Layer
```

The system should not silently transform a retrieval failure into a
confident generated answer.

------------------------------------------------------------------------

# 41. Performance Considerations

End-to-end latency can be divided into:

``` text
Total Latency
=
Query Processing
+
Retrieval
+
Re-ranking
+
Context Construction
+
LLM Generation
+
Citation/Validation
```

Each component should be measurable.

This allows bottlenecks to be identified independently.

------------------------------------------------------------------------

# 42. Modularity

Each major RAG component should be replaceable.

``` text
Embedding Model
      ↓
Replaceable

Vector Database
      ↓
Replaceable

BM25 Engine
      ↓
Replaceable

Re-ranker
      ↓
Replaceable

LLM
      ↓
Replaceable
```

This prevents the framework from becoming tightly coupled to a single
model or vendor.

------------------------------------------------------------------------

# 43. Recommended Initial Implementation Order

## Phase 1 --- Baseline

``` text
Document Loading
      ↓
Text Extraction
      ↓
Chunking
      ↓
Embeddings
      ↓
Vector DB
      ↓
Vector Retrieval
      ↓
LLM
      ↓
Basic Citations
```

## Phase 2 --- Hybrid Retrieval

``` text
BM25
+
Vector Search
↓
Fusion
```

## Phase 3 --- Retrieval Enhancement

``` text
Metadata Filtering
+
Re-ranking
```

## Phase 4 --- Grounding

``` text
Evidence Validation
+
No-answer Handling
+
Citation Verification
```

## Phase 5 --- Evaluation

``` text
Benchmark Dataset
+
Retrieval Metrics
+
Answer Metrics
+
Grounding Metrics
+
Latency
```

## Phase 6 --- Advanced Experiments

Only if justified by evaluation:

``` text
Query Rewriting
Adaptive Retrieval
Context Compression
Multi-document Reasoning
Version-aware Retrieval
```

------------------------------------------------------------------------

# 44. Final Architecture

The intended mature architecture is:

``` text
                         ┌───────────────────────┐
                         │ University Documents  │
                         └───────────┬───────────┘
                                     │
                                     ▼
                           Document Ingestion
                                     │
                                     ▼
                         Processing + Chunking
                                     │
                                     ▼
                          Metadata + Provenance
                                     │
                         ┌───────────┴───────────┐
                         ▼                       ▼
                    Embeddings               BM25 Index
                         │                       │
                         ▼                       │
                   Vector Store                  │
                         │                       │
                         └───────────┬───────────┘
                                     │
                              Student Query
                                     │
                                     ▼
                              Query Analysis
                                     │
                         ┌───────────┴───────────┐
                         ▼                       ▼
                  Dense Retrieval          Lexical Retrieval
                         │                       │
                         └───────────┬───────────┘
                                     ▼
                              Candidate Fusion
                                     │
                                     ▼
                             Metadata Filtering
                                     │
                                     ▼
                                Re-ranking
                                     │
                                     ▼
                             Evidence Selection
                                     │
                                     ▼
                           Context Construction
                                     │
                                     ▼
                                LLM Layer
                                     │
                                     ▼
                            Grounding Validation
                                     │
                                     ▼
                           Citation Construction
                                     │
                                     ▼
                           Answer + Sources
                                     │
                                     ▼
                                Evaluation
```

------------------------------------------------------------------------

# 45. Architectural Definition

The RAG architecture of SRU Assistant is defined as:

> **A modular Hybrid RAG framework that combines semantic vector
> retrieval and lexical retrieval over institutionally sourced academic
> documents, enriches retrieval using metadata and relevance re-ranking,
> constructs an explicit evidence context for LLM generation, and
> produces source-grounded answers with traceable citations.**

The system's primary objective is not to make the LLM appear
knowledgeable.

Its objective is to make the answer **retrievable, evidence-grounded,
traceable, and measurable**.

------------------------------------------------------------------------

# 46. Design Rule

The framework should always follow:

``` text
                    KNOWLEDGE
                       │
                       ▼
                    RETRIEVE
                       │
                       ▼
                    VERIFY
                       │
                       ▼
                    GENERATE
                       │
                       ▼
                     CITE
                       │
                       ▼
                   EVALUATE
```

**SRU Assistant = Retrieval + Evidence + Generation + Traceability +
Evaluation.**
