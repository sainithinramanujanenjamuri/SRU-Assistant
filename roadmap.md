# SRU Assistant --- Development Roadmap

## 1. Roadmap Purpose

This roadmap defines the phased development plan for **SRU Assistant: A
RAG Framework for University Academic Query Resolution**.

The roadmap is designed to build the system incrementally:

``` text
Foundation
    ↓
Document Knowledge Base
    ↓
Baseline RAG
    ↓
Hybrid Retrieval
    ↓
Advanced Retrieval
    ↓
Grounded Generation
    ↓
Citation & Validation
    ↓
Evaluation
    ↓
Application & Deployment
    ↓
Research / Optimization
```

The project should not attempt to implement every advanced RAG technique
at the beginning.

Each phase should produce a working, testable result before the next
layer is added.

------------------------------------------------------------------------

# 2. Development Philosophy

SRU Assistant will be developed as a **modular RAG framework**, not
merely as a chatbot connected to a vector database.

The development principle is:

``` text
Build
  ↓
Test
  ↓
Measure
  ↓
Improve
  ↓
Document
  ↓
Proceed
```

Every major phase should have:

-   Implementation
-   Unit tests
-   Integration tests where applicable
-   Demonstration
-   Metrics where applicable
-   Documentation
-   Clear completion criteria

------------------------------------------------------------------------

# 3. Phase Overview

  -----------------------------------------------------------------------
  Phase                   Name                    Primary Outcome
  ----------------------- ----------------------- -----------------------
  0                       Project Foundation      Repository and
                                                  engineering foundation

  1                       Document Intelligence   Reliable document
                                                  ingestion and
                                                  extraction

  2                       Knowledge Preparation   Chunking, metadata,
                                                  provenance

  3                       Embedding & Vector      Searchable semantic
                          Store                   knowledge base

  4                       Baseline RAG            End-to-end vector RAG

  5                       Hybrid Retrieval        Vector + BM25 retrieval

  6                       Retrieval Enhancement   Metadata filtering +
                                                  re-ranking

  7                       Grounded Generation     Evidence-controlled LLM
                                                  responses

  8                       Citation & Provenance   Traceable source
                                                  citations

  9                       RAG Evaluation          Benchmark and
                                                  quantitative evaluation

  10                      Application Layer       Student-facing web
                                                  application

  11                      Reliability & Security  Robustness, validation,
                                                  and safeguards

  12                      Advanced RAG Research   Experimental
                                                  improvements

  13                      Final Integration       Complete capstone
                                                  system

  14                      Deployment &            Deployable and
                          Demonstration           presentation-ready
                                                  system
  -----------------------------------------------------------------------

------------------------------------------------------------------------

# PHASE 0 --- PROJECT FOUNDATION

## Objective

Establish a clean and reproducible engineering foundation.

## Tasks

### Repository

Create the initial structure:

``` text
sru-assistant/
├── app/
├── ingestion/
├── retrieval/
├── generation/
├── citations/
├── evaluation/
├── documents/
├── tests/
├── frontend/
├── scripts/
├── configs/
├── README.md
├── framework.md
├── RAG.md
└── roadmap.md
```

### Environment

Set up:

-   Python environment
-   Dependency management
-   Configuration management
-   Environment variables
-   Logging
-   Basic error handling

### Engineering Standards

Establish:

-   Formatting
-   Linting
-   Type checking where practical
-   Testing framework
-   Git workflow
-   Documentation conventions

## Deliverables

-   Working repository
-   Environment setup
-   Initial README
-   Test framework
-   Configuration system

## Definition of Done

``` text
Project can be cloned
       ↓
Environment can be created
       ↓
Dependencies install
       ↓
Tests execute
       ↓
Application skeleton starts
```

------------------------------------------------------------------------

# PHASE 1 --- DOCUMENT INTELLIGENCE

## Objective

Build the document ingestion pipeline.

## Tasks

### Document Discovery

Collect the initial official SR University academic documents.

Priority:

1.  Academic calendars
2.  Examination schedules
3.  Course structures
4.  Syllabi
5.  Examination guidelines
6.  Department notices

### Document Validation

Check:

-   File type
-   File readability
-   Empty documents
-   Corrupted files
-   Duplicate documents

### Text Extraction

Build loaders for the required document formats.

Initial priority:

``` text
PDF
DOCX
TXT
```

### Cleaning

Normalize:

-   Whitespace
-   Repeated headers
-   Footers
-   Page artifacts
-   Broken line structures

Preserve academically meaningful structure.

## Deliverables

``` text
documents/
    raw/
    processed/
```

plus an ingestion pipeline.

## Definition of Done

A source document can be converted into structured text without losing
important academic information.

------------------------------------------------------------------------

# PHASE 2 --- KNOWLEDGE PREPARATION

## Objective

Transform processed documents into retrieval-ready chunks.

## Tasks

### Structure Detection

Identify:

-   Titles
-   Headings
-   Sections
-   Tables
-   Page boundaries
-   Academic entities

### Chunking

Implement the baseline chunking strategy.

Track:

``` text
chunk_id
document_id
text
page
section
```

### Metadata

Add metadata such as:

``` text
department
program
semester
academic_year
document_type
source
version
```

### Provenance

Ensure every chunk can be traced back to its original document and page.

## Deliverables

A structured chunk dataset.

Example:

``` json
{
  "chunk_id": "chunk_001",
  "document_id": "doc_001",
  "text": "...",
  "metadata": {
    "department": "CSE",
    "semester": "VII",
    "academic_year": "2026-27",
    "page": 3
  }
}
```

## Definition of Done

Every chunk is independently retrievable and traceable to its source.

------------------------------------------------------------------------

# PHASE 3 --- EMBEDDING & VECTOR STORE

## Objective

Build the semantic knowledge base.

## Tasks

### Embedding Model

Select and benchmark an embedding model.

Consider:

-   Semantic quality
-   Academic terminology
-   Local execution
-   Speed
-   Memory requirements

### Vector Database

Select a vector store suitable for:

-   Local development
-   Metadata filtering
-   Similarity search
-   Persistent storage
-   Future scaling

### Indexing

Build:

``` text
Chunk
 ↓
Embedding
 ↓
Vector
 ↓
Vector Database
```

### Retrieval API

Implement a basic:

``` text
search(query, top_k)
```

interface.

## Deliverables

-   Embedding pipeline
-   Persistent vector index
-   Basic semantic search
-   Retrieval API

## Definition of Done

A natural-language query can retrieve relevant academic chunks.

------------------------------------------------------------------------

# PHASE 4 --- BASELINE RAG

## Objective

Create the first complete end-to-end RAG system.

## Architecture

``` text
User Query
    ↓
Query Embedding
    ↓
Vector Search
    ↓
Top-K Chunks
    ↓
Context Builder
    ↓
LLM
    ↓
Answer
```

## Tasks

### Query Interface

Accept natural-language queries.

### Retrieval

Retrieve top-K semantic results.

### Context Builder

Convert retrieved chunks into structured LLM context.

### Prompt

Implement a grounded generation prompt.

Basic rule:

``` text
Answer using the provided evidence.
Do not invent university-specific facts.
```

### Response

Return:

``` text
answer
+
basic source information
```

## Deliverables

A working baseline RAG application.

## Definition of Done

A student can ask a question and receive an answer based on retrieved
university documents.

------------------------------------------------------------------------

# PHASE 5 --- HYBRID RETRIEVAL

## Objective

Improve retrieval by combining semantic and lexical search.

## Architecture

``` text
                 Query
                   │
          ┌────────┴────────┐
          ▼                 ▼
    Vector Search        BM25 Search
          │                 │
          └────────┬────────┘
                   ▼
              Fusion
                   ↓
          Unified Candidates
```

## Tasks

### BM25

Implement lexical retrieval.

### Candidate Fusion

Experiment with:

-   Weighted score fusion
-   Reciprocal Rank Fusion

### Query-Type Analysis

Test performance on:

-   Semantic questions
-   Course codes
-   Dates
-   Regulation numbers
-   Names
-   Exact academic terms

## Deliverables

Hybrid retriever.

## Definition of Done

The system can retrieve candidates using both semantic and lexical
signals.

------------------------------------------------------------------------

# PHASE 6 --- RETRIEVAL ENHANCEMENT

## Objective

Improve the quality of evidence passed to the LLM.

## Tasks

### Metadata Filtering

Support constraints such as:

``` text
department
semester
academic_year
document_type
program
```

### Re-ranking

Pipeline:

``` text
Hybrid Retrieval
      ↓
Candidate Pool
      ↓
Re-ranker
      ↓
Top Relevant Evidence
```

### Top-K Experiments

Evaluate different values of K.

Example:

``` text
K = 3
K = 5
K = 10
K = 15
```

Do not assume that larger K is always better.

## Deliverables

Enhanced retrieval pipeline.

## Definition of Done

Retrieval quality is measurably evaluated and the selected configuration
is justified by results.

------------------------------------------------------------------------

# PHASE 7 --- GROUNDED GENERATION

## Objective

Make the LLM reliably operate over retrieved evidence.

## Tasks

### Evidence-First Prompting

Provide:

``` text
User Query
+
Retrieved Evidence
+
Generation Rules
```

### Grounding Rules

Implement:

-   No unsupported university-specific claims
-   Explicit insufficient-evidence handling
-   Preservation of exact dates and identifiers
-   Conflict awareness

### No-Answer Behavior

If evidence is insufficient:

``` text
I couldn't find sufficient information in the
available SR University documents to answer this accurately.
```

### Multi-Document Answers

Support answers requiring multiple sources.

## Deliverables

Grounded generation layer.

## Definition of Done

The model does not simply answer from general pretrained knowledge when
university evidence is unavailable.

------------------------------------------------------------------------

# PHASE 8 --- CITATION & PROVENANCE

## Objective

Make every grounded answer traceable.

## Pipeline

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

## Tasks

### Citation Data Model

Define:

``` text
citation_id
document_id
document_name
page
section
chunk_id
source
```

### Citation Rendering

Example:

``` text
The examination begins on September 12.

Source:
Academic Calendar 2026-27 — Page 3
```

### Citation Verification

Investigate whether generated claims are actually supported by cited
chunks.

## Deliverables

Source-aware response system.

## Definition of Done

A user can identify the document and location supporting an answer.

------------------------------------------------------------------------

# PHASE 9 --- RAG EVALUATION

## Objective

Turn the system into a measurable research project.

This phase is critical for the capstone.

## Tasks

### Benchmark Dataset

Create a university-specific question dataset.

Categories:

``` text
Direct factual
Date-based
Course-related
Regulation
Department-specific
Multi-document
Paraphrased
Ambiguous
Out-of-knowledge-base
Version-sensitive
```

### Ground Truth

Where possible, record:

``` text
question
expected answer
supporting document
supporting page
supporting chunk
```

### Retrieval Metrics

Measure:

-   Recall@K
-   Precision@K
-   MRR
-   nDCG

### Generation Metrics

Measure:

-   Correctness
-   Relevance
-   Completeness
-   Groundedness

### Citation Metrics

Measure:

-   Citation correctness
-   Citation completeness
-   Evidence support

### Hallucination Metrics

Measure unsupported factual claims.

### Latency

Measure:

``` text
Query processing
+
Retrieval
+
Re-ranking
+
Generation
+
Validation
```

## Baseline Experiments

Compare:

``` text
Experiment A:
Vector RAG

Experiment B:
Hybrid RAG

Experiment C:
Hybrid + Re-ranking

Experiment D:
Hybrid + Re-ranking + Grounding Validation
```

## Definition of Done

The project has quantitative evidence showing how retrieval and
generation configurations perform.

------------------------------------------------------------------------

# PHASE 10 --- APPLICATION LAYER

## Objective

Build the student-facing SRU Assistant application.

## Core UI

``` text
┌────────────────────────────────────────────┐
│              SRU ASSISTANT                │
├────────────────────────────────────────────┤
│                                            │
│  Ask an academic question...              │
│                                            │
│  [ What is my VII semester exam date? ]   │
│                                            │
│                    [Ask]                  │
│                                            │
├────────────────────────────────────────────┤
│ Answer                                     │
│                                            │
│ ...                                        │
│                                            │
│ Sources                                    │
│ • Academic Calendar — Page 3              │
└────────────────────────────────────────────┘
```

## Features

Initial:

-   Query input
-   Answer display
-   Source display
-   Loading state
-   Error state

Later:

-   Citation expansion
-   Document preview
-   Conversation history
-   Feedback
-   Search filters

## Definition of Done

A student can interact with SRU Assistant without interacting directly
with the backend.

------------------------------------------------------------------------

# PHASE 11 --- RELIABILITY & SECURITY

## Objective

Make the system robust enough for real usage and demonstration.

## Document Security

Implement as appropriate:

-   File validation
-   Trusted source restrictions
-   Duplicate detection
-   Upload controls
-   Document integrity checks

## Query Safety

Handle:

-   Empty queries
-   Extremely long queries
-   Unsupported requests
-   Prompt injection attempts
-   Malformed input

## Retrieval Safety

Prevent:

-   Untrusted content becoming authoritative
-   Missing provenance
-   Invalid metadata
-   Broken document references

## Generation Safety

Ensure:

``` text
No Evidence
    ↓
No Confident University Answer
```

## Observability

Track:

``` text
request_id
query
retrieval_count
retrieved_documents
latency
model
errors
citation_count
```

Sensitive data should not be logged unnecessarily.

## Definition of Done

The application fails safely and provides enough diagnostic information
to identify problems.

------------------------------------------------------------------------

# PHASE 12 --- ADVANCED RAG RESEARCH

## Objective

Experiment with advanced techniques only after the baseline and hybrid
systems have been measured.

Potential experiments:

### Query Rewriting

``` text
User Query
    ↓
Query Rewriter
    ↓
Improved Search Query
    ↓
Retrieval
```

### Multi-Query Retrieval

Generate multiple search formulations and combine results.

### Context Compression

Reduce irrelevant information before LLM generation.

### Parent-Child Retrieval

Retrieve a precise child chunk while providing a larger parent context.

### Adaptive Top-K

Select the number of retrieved chunks according to query complexity.

### Adaptive Retrieval Weights

Adjust:

``` text
semantic weight
+
lexical weight
```

depending on query characteristics.

### Version-Aware Retrieval

Prefer documents matching the requested academic year or current
version.

### Conflict Detection

Identify when different documents provide conflicting information.

### Citation Verification

Validate that citations support generated claims.

## Research Rule

Do not add advanced components simply because they are popular.

Each addition should answer:

> **Does this improve retrieval, grounding, citation quality, accuracy,
> or efficiency on our benchmark?**

------------------------------------------------------------------------

# PHASE 13 --- FINAL INTEGRATION

## Objective

Combine the validated components into the final SRU Assistant framework.

## Final Architecture

``` text
                  OFFICIAL DOCUMENTS
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
              ┌──────────┴──────────┐
              ▼                     ▼
         Embeddings               BM25
              │                     │
              ▼                     ▼
        Vector Store          Lexical Index
              │                     │
              └──────────┬──────────┘
                         ▼
                    User Query
                         │
                         ▼
                  Query Analysis
                         │
                         ▼
                 Hybrid Retrieval
                         │
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
                       LLM
                         │
                         ▼
                Grounding Validation
                         │
                         ▼
                Citation Construction
                         │
                         ▼
                 Final Answer
                         │
                         ▼
                    Evaluation
```

## Integration Tasks

-   Connect all modules
-   Remove temporary prototypes
-   Standardize interfaces
-   Centralize configuration
-   Add end-to-end tests
-   Add failure handling
-   Verify citations
-   Verify retrieval
-   Verify UI/API integration

## Definition of Done

The complete system operates as one coherent application.

------------------------------------------------------------------------

# PHASE 14 --- DEPLOYMENT & DEMONSTRATION

## Objective

Prepare the project for final capstone evaluation.

## Deployment

Prepare:

``` text
Frontend
    ↓
Backend
    ↓
RAG Pipeline
    ↓
Vector Store
    ↓
LLM
```

Deployment architecture depends on the final infrastructure and model
choices.

## Documentation

Complete:

-   README
-   Architecture documentation
-   RAG documentation
-   API documentation
-   Installation guide
-   Dataset documentation
-   Evaluation methodology
-   Results
-   Limitations
-   Future work

## Demonstration Scenario

Prepare a controlled demonstration covering:

### Demo 1 --- Basic Question

``` text
Question
 ↓
Retrieval
 ↓
Answer
 ↓
Citation
```

### Demo 2 --- Exact Course Code

Demonstrate lexical retrieval.

### Demo 3 --- Paraphrased Question

Demonstrate semantic retrieval.

### Demo 4 --- Multi-Document Question

Demonstrate evidence synthesis.

### Demo 5 --- Unsupported Question

Demonstrate controlled no-answer behavior.

### Demo 6 --- Citation

Open the cited source and show the supporting material.

------------------------------------------------------------------------

# 4. Milestone Gates

A phase should not automatically proceed merely because its code exists.

Each phase has a gate.

``` text
Implementation
     ↓
Tests
     ↓
Validation
     ↓
Documentation
     ↓
Gate
     ↓
Next Phase
```

------------------------------------------------------------------------

# 5. Recommended Phase Dependencies

``` text
Phase 0
  │
  ▼
Phase 1
  │
  ▼
Phase 2
  │
  ▼
Phase 3
  │
  ▼
Phase 4
  │
  ▼
Phase 5
  │
  ▼
Phase 6
  │
  ▼
Phase 7
  │
  ▼
Phase 8
  │
  ▼
Phase 9
  │
  ├──────────────► Phase 12
  │
  ▼
Phase 10
  │
  ▼
Phase 11
  │
  ▼
Phase 13
  │
  ▼
Phase 14
```

Phase 12 can be performed iteratively alongside later integration once a
reliable evaluation benchmark exists.

------------------------------------------------------------------------

# 6. Minimum Viable Product

The first usable version should be:

``` text
Official Documents
       ↓
Extraction
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
Citation
       ↓
Student UI
```

This corresponds primarily to:

``` text
Phase 0 → Phase 4 → Phase 8 → Phase 10
```

However, the system should not be considered the final research version
until it has been evaluated.

------------------------------------------------------------------------

# 7. Research-Grade Target

The final target is:

``` text
Official University Documents
          ↓
Document Intelligence
          ↓
Structure-Aware Chunking
          ↓
Metadata + Provenance
          ↓
Dense + Lexical Retrieval
          ↓
Candidate Fusion
          ↓
Metadata Filtering
          ↓
Re-ranking
          ↓
Evidence Selection
          ↓
Grounded LLM Generation
          ↓
Grounding Validation
          ↓
Citation Verification
          ↓
Answer + Sources
          ↓
Quantitative Evaluation
```

------------------------------------------------------------------------

# 8. Completion Checklist

## Foundation

-   [ ] Repository created
-   [ ] Environment configured
-   [ ] Testing configured
-   [ ] Logging configured
-   [ ] Documentation structure created

## Documents

-   [ ] Official documents collected
-   [ ] Document loaders implemented
-   [ ] Text extraction validated
-   [ ] Cleaning implemented
-   [ ] Metadata extraction implemented
-   [ ] Provenance preserved

## Knowledge Base

-   [ ] Chunking implemented
-   [ ] Embedding model selected
-   [ ] Vector database configured
-   [ ] Indexing pipeline implemented
-   [ ] Search API implemented

## RAG

-   [ ] Baseline vector RAG works
-   [ ] BM25 retrieval works
-   [ ] Hybrid fusion works
-   [ ] Metadata filtering works
-   [ ] Re-ranking evaluated
-   [ ] Evidence builder works
-   [ ] Grounded generation works

## Citations

-   [ ] Source metadata preserved
-   [ ] Citations generated
-   [ ] Citation display implemented
-   [ ] Citation support evaluated

## Evaluation

-   [ ] Benchmark dataset created
-   [ ] Ground truth established
-   [ ] Retrieval metrics implemented
-   [ ] Answer evaluation implemented
-   [ ] Grounding evaluation implemented
-   [ ] Citation evaluation implemented
-   [ ] Latency measured
-   [ ] Baseline vs enhanced results documented

## Application

-   [ ] Backend API works
-   [ ] Frontend works
-   [ ] Error states handled
-   [ ] Sources visible
-   [ ] End-to-end testing complete

## Finalization

-   [ ] Security checks complete
-   [ ] Documentation complete
-   [ ] Deployment prepared
-   [ ] Demonstration scenarios prepared
-   [ ] Final evaluation results documented
-   [ ] Limitations documented
-   [ ] Future work documented

------------------------------------------------------------------------

# 9. Final Project Evolution

The project should evolve through the following progression:

``` text
               STAGE 1
             Basic RAG
                 │
                 ▼
        STAGE 2
       Hybrid RAG
                 │
                 ▼
        STAGE 3
    Retrieval Enhancement
                 │
                 ▼
        STAGE 4
    Grounded Generation
                 │
                 ▼
        STAGE 5
  Citation + Provenance
                 │
                 ▼
        STAGE 6
 Quantitative Evaluation
                 │
                 ▼
        STAGE 7
    Advanced RAG Research
                 │
                 ▼
        STAGE 8
 Complete SRU Assistant
```

The objective is not to maximize the number of components.

The objective is to build a system in which every major component has a
clear purpose, measurable behavior, and testable interface.

------------------------------------------------------------------------

# 10. Roadmap Definition

The complete development strategy can be summarized as:

> **Build a reliable baseline RAG first, introduce hybrid retrieval,
> improve evidence selection, enforce grounded generation, make every
> answer traceable through citations, and quantitatively evaluate each
> improvement before adopting it into the final SRU Assistant
> framework.**

**SRU Assistant development principle:**

``` text
SOURCE
  ↓
PROCESS
  ↓
INDEX
  ↓
RETRIEVE
  ↓
RERANK
  ↓
GROUND
  ↓
CITE
  ↓
EVALUATE
  ↓
IMPROVE
```
