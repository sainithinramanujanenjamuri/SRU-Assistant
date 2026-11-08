# SRU Assistant --- CODEX AGENT INSTRUCTIONS

## 0. Purpose of This File

This file is the **primary implementation instruction for Codex**
working on the SRU Assistant project.

Codex must use this file together with:

``` text
framework.md
RAG.md
roadmap.md
```

These documents define the project's architecture, RAG design,
development phases, boundaries, and completion criteria.

The purpose of this file is to prevent implementation drift, missing
requirements, accidental scope expansion, and inconsistent architecture.

------------------------------------------------------------------------

# 1. PROJECT IDENTITY

## Official Project Title

**SRU Assistant: A RAG Framework for University Academic Query
Resolution**

## Project Type

Capstone Project

## Domain

-   Artificial Intelligence
-   Natural Language Processing
-   Retrieval-Augmented Generation
-   Information Retrieval
-   University Academic Information Systems

------------------------------------------------------------------------

# 2. ABSOLUTE PROJECT BOUNDARY

## SRU Assistant is a completely independent project.

DO NOT import architecture, terminology, implementation assumptions, or
design concepts from:

-   RYU AI Framework
-   RYU Runtime
-   RYU Spaces
-   RYU Workers
-   RYU Agents
-   RYU autonomous systems
-   RYU cognitive architecture
-   RYU memory architecture
-   RYU orchestration architecture

The previous RYU project is **not this project**.

If a design decision is not justified by the SRU Assistant requirements,
framework.md, RAG.md, roadmap.md, or an explicit user instruction, do
not introduce it simply because it existed in another project.

------------------------------------------------------------------------

# 3. SOURCE OF TRUTH

Codex must treat the project documentation as the primary specification.

Read and follow:

``` text
framework.md
RAG.md
roadmap.md
agent.md
```

Priority:

``` text
Explicit current user instruction
        ↓
Project-specific requirements
        ↓
framework.md
        ↓
RAG.md
        ↓
roadmap.md
        ↓
Existing implementation
        ↓
General engineering assumptions
```

When a conflict exists, do not silently choose a side.

Stop and clearly identify the conflict before making a destructive
architectural decision.

------------------------------------------------------------------------

# 4. CORE PROJECT OBJECTIVE

Build a **modular, source-grounded RAG framework** that answers SR
University academic questions using official university documents.

The system should:

1.  Ingest institutional documents.
2.  Extract and process their content.
3.  Preserve document structure.
4.  Create meaningful chunks.
5.  Attach metadata and provenance.
6.  Generate embeddings.
7.  Store searchable vectors.
8.  Perform semantic retrieval.
9.  Perform lexical retrieval.
10. Fuse retrieval candidates.
11. Apply metadata-aware filtering.
12. Re-rank candidates.
13. Construct evidence context.
14. Generate an answer using an LLM.
15. Prevent unsupported university-specific claims.
16. Provide source citations.
17. Validate grounding where implemented.
18. Measure retrieval and answer quality.
19. Provide a usable student-facing application.
20. Remain extensible to additional departments and document types.

------------------------------------------------------------------------

# 5. CENTRAL DESIGN PRINCIPLE

Always preserve:

``` text
RETRIEVE FIRST
      ↓
USE EVIDENCE
      ↓
GENERATE
      ↓
CITE
      ↓
EVALUATE
```

The LLM is not the authoritative source of university information.

The institutional document collection is the knowledge source.

------------------------------------------------------------------------

# 6. TARGET ARCHITECTURE

The mature system should follow this conceptual architecture:

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

Not every advanced component must be implemented immediately.

Follow the roadmap phases.

------------------------------------------------------------------------

# 7. REQUIRED DEVELOPMENT STRATEGY

Build incrementally.

Never attempt to build the final architecture in one uncontrolled
implementation.

Follow:

``` text
Phase
  ↓
Implement
  ↓
Test
  ↓
Validate
  ↓
Document
  ↓
Measure where applicable
  ↓
Next Phase
```

A component should not be considered complete merely because its code
runs.

------------------------------------------------------------------------

# 8. ROADMAP

## Phase 0 --- Project Foundation

Build:

-   Repository structure
-   Python environment
-   Dependency management
-   Configuration
-   Environment variables
-   Logging
-   Error handling
-   Formatting/linting
-   Testing
-   Initial documentation

Definition of done:

``` text
Environment works
Dependencies install
Tests run
Application skeleton starts
```

------------------------------------------------------------------------

## Phase 1 --- Document Intelligence

Build:

-   Document discovery
-   Document validation
-   PDF loading
-   DOCX loading where required
-   TXT loading where required
-   Text extraction
-   Cleaning
-   Structure preservation
-   Duplicate detection where applicable

Prioritize actual SR University source documents.

Do not fabricate institutional documents.

------------------------------------------------------------------------

## Phase 2 --- Knowledge Preparation

Build:

-   Structure detection
-   Chunking
-   Chunk metadata
-   Page tracking
-   Section tracking
-   Document identifiers
-   Provenance

Every chunk must remain traceable to its original source.

Conceptual metadata:

``` text
chunk_id
document_id
document_name
page
section
department
program
semester
academic_year
document_type
source
version
```

Do not unnecessarily invent metadata that cannot be supported by the
source.

------------------------------------------------------------------------

## Phase 3 --- Embedding & Vector Store

Build:

-   Embedding pipeline
-   Embedding model interface
-   Vector storage
-   Persistence
-   Metadata storage
-   Similarity search
-   Retrieval API

Provide a clean abstraction so the embedding model and vector database
can be replaced later.

Example conceptual interface:

``` text
embed(text)
index(chunks)
search(query, top_k, filters)
```

Exact APIs depend on implementation.

------------------------------------------------------------------------

## Phase 4 --- Baseline RAG

Build the first complete RAG system:

``` text
Query
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

The baseline must work before hybrid retrieval is introduced.

The baseline should establish a measurable reference point.

------------------------------------------------------------------------

## Phase 5 --- Hybrid Retrieval

Add:

``` text
Vector Search
+
BM25 / Lexical Search
```

Then combine results.

Possible fusion methods:

-   Weighted score fusion
-   Reciprocal Rank Fusion

Do not assume one method is superior without evaluation.

------------------------------------------------------------------------

## Phase 6 --- Retrieval Enhancement

Add and evaluate:

-   Metadata filtering
-   Re-ranking
-   Top-K tuning
-   Query analysis

Possible metadata:

``` text
department
program
semester
academic_year
document_type
```

Avoid filters that can accidentally remove the correct evidence.

------------------------------------------------------------------------

## Phase 7 --- Grounded Generation

Implement:

-   Evidence-first prompting
-   Strict evidence boundaries
-   No-answer handling
-   Multi-document context
-   Conflict awareness
-   Exact academic information preservation

Required behavior:

``` text
Sufficient Evidence
      ↓
Generate grounded answer

Insufficient Evidence
      ↓
Do not fabricate
```

Example controlled response:

> I couldn't find sufficient information in the available SR University
> documents to answer this accurately.

------------------------------------------------------------------------

## Phase 8 --- Citation & Provenance

Preserve:

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
Answer
 ↓
Citation
```

Citations should identify the source document and location wherever
available.

Do not generate fake page numbers, sections, or source names.

------------------------------------------------------------------------

## Phase 9 --- RAG Evaluation

Create a benchmark dataset.

Categories should include:

1.  Direct factual questions
2.  Date-based questions
3.  Course-related questions
4.  Regulation questions
5.  Department-specific questions
6.  Multi-document questions
7.  Paraphrased questions
8.  Ambiguous questions
9.  Out-of-knowledge-base questions
10. Version-sensitive questions

Evaluate retrieval using:

-   Recall@K
-   Precision@K
-   MRR
-   nDCG

Evaluate answers using:

-   Correctness
-   Relevance
-   Completeness
-   Groundedness

Evaluate citations using:

-   Citation correctness
-   Citation completeness
-   Evidence support

Measure latency.

------------------------------------------------------------------------

## Phase 10 --- Application Layer

Build a student-facing application.

Minimum:

-   Query input
-   Answer display
-   Source display
-   Loading state
-   Error state

Later features may include:

-   Citation expansion
-   Source/document preview
-   Conversation history
-   Feedback
-   Search filters

Do not allow UI complexity to obscure the RAG pipeline.

------------------------------------------------------------------------

## Phase 11 --- Reliability & Security

Handle:

-   Invalid files
-   Duplicate files
-   Empty documents
-   Empty queries
-   Long queries
-   Malformed input
-   Unsupported questions
-   Prompt injection attempts
-   Missing provenance
-   Invalid metadata
-   Retrieval failures
-   LLM failures

Implement appropriate:

-   Logging
-   Request IDs
-   Error handling
-   Source restrictions
-   File validation
-   Audit information

Do not log sensitive information unnecessarily.

------------------------------------------------------------------------

## Phase 12 --- Advanced RAG Research

Only after reliable baseline and evaluation.

Potential experiments:

-   Query rewriting
-   Multi-query retrieval
-   Context compression
-   Parent-child retrieval
-   Adaptive top-K
-   Adaptive retrieval weights
-   Version-aware retrieval
-   Conflict detection
-   Citation verification

Every advanced feature must have a reason and measurable evaluation.

Do not add advanced techniques for appearance alone.

------------------------------------------------------------------------

## Phase 13 --- Final Integration

Integrate:

-   Ingestion
-   Processing
-   Chunking
-   Metadata
-   Embeddings
-   Vector store
-   BM25
-   Hybrid retrieval
-   Filtering
-   Re-ranking
-   Evidence builder
-   LLM
-   Grounding validation
-   Citations
-   Evaluation
-   API
-   Frontend

Then run end-to-end tests.

------------------------------------------------------------------------

## Phase 14 --- Deployment & Demonstration

Prepare:

-   Deployment
-   README
-   Installation instructions
-   Architecture documentation
-   RAG documentation
-   API documentation
-   Dataset documentation
-   Evaluation methodology
-   Results
-   Limitations
-   Future work
-   Demonstration scenarios

------------------------------------------------------------------------

# 9. RAG ARCHITECTURE RULES

## Rule 1 --- Source Grounding

University-specific factual answers should come from retrieved
institutional evidence.

## Rule 2 --- No Fabrication

Never invent:

-   University policies
-   Dates
-   Exam schedules
-   Course information
-   Faculty information
-   Department information
-   Regulations
-   Source documents
-   Page numbers
-   Citations

## Rule 3 --- Evidence Boundary

The LLM should receive explicitly marked evidence.

## Rule 4 --- Provenance

Every retrieved chunk must retain its origin.

## Rule 5 --- Citation Integrity

A citation must correspond to the evidence used.

## Rule 6 --- Insufficient Evidence

If evidence is insufficient, return a controlled response rather than
guessing.

## Rule 7 --- Conflicting Evidence

Do not silently resolve conflicting institutional sources.

Surface the conflict and identify the relevant sources.

------------------------------------------------------------------------

# 10. RETRIEVAL RULES

The intended retrieval system is:

``` text
Semantic Retrieval
        +
Lexical Retrieval
        ↓
Candidate Fusion
        ↓
Metadata Filtering
        ↓
Re-ranking
        ↓
Evidence Selection
```

Do not replace this with pure vector retrieval after Phase 5 unless
explicitly instructed.

Do not introduce a different retrieval architecture without documenting
the reason.

------------------------------------------------------------------------

# 11. DOCUMENT RULES

Documents are the foundation of the knowledge base.

The system must preserve:

``` text
Source
Document
Page
Section
Chunk
Metadata
```

Do not destroy page boundaries during preprocessing if page-level
citations are required.

Do not aggressively clean text if doing so removes academic meaning.

Tables require special care.

Course codes, dates, regulation numbers, names, and identifiers must not
be normalized into incorrect forms.

------------------------------------------------------------------------

# 12. CHUNKING RULES

Chunking should optimize retrieval quality, not simply satisfy a fixed
token count.

Start with a reproducible baseline.

Track:

``` text
chunk_size
chunk_overlap
document
page
section
```

Evaluate alternatives later.

Do not change chunking parameters randomly between experiments.

------------------------------------------------------------------------

# 13. EMBEDDING RULES

The embedding model must be treated as a replaceable component.

Evaluate candidate models using the project benchmark.

Record:

``` text
model
dimension
retrieval configuration
latency
evaluation result
```

Do not claim that an embedding model is optimal without measurement.

------------------------------------------------------------------------

# 14. LLM RULES

The LLM is a generation layer over retrieved evidence.

It must not become an unrestricted university knowledge source.

The generation prompt should enforce:

``` text
Use supplied evidence.
Do not fabricate university-specific information.
If evidence is insufficient, say so.
Preserve exact academic facts.
Use source information for citations.
```

The exact prompt can evolve through evaluation.

------------------------------------------------------------------------

# 15. AGENT / ORCHESTRATOR ROLE

The SRU Assistant agent is a **workflow coordinator for the RAG
pipeline**.

It is NOT:

-   A general autonomous agent
-   A multi-agent framework
-   An autonomous software engineer
-   An RYU agent
-   A worker system
-   A persistent autonomous process

Its conceptual responsibility is:

``` text
Understand Query
      ↓
Select Retrieval Strategy
      ↓
Retrieve Evidence
      ↓
Assess Evidence
      ↓
Construct Context
      ↓
Request Generation
      ↓
Validate Grounding
      ↓
Attach Citations
      ↓
Return Answer
```

The agent should make bounded decisions necessary for the RAG workflow.

Avoid autonomous behavior outside the project's scope.

------------------------------------------------------------------------

# 16. QUERY TYPES

The system should be designed to support:

### Direct factual

> "What is the attendance requirement?"

### Date-based

> "When are the mid-semester exams?"

### Course-related

> "What subjects are in this semester?"

### Identifier-based

> "What is 23CSE302T?"

### Department-specific

> "What is the CSE examination schedule?"

### Multi-document

> "What subjects do I have and when are their exams?"

### Paraphrased

> "When do my mid exams begin?"

### Ambiguous

Questions where additional context may be necessary.

### Out-of-knowledge-base

Questions for which the indexed documents contain no reliable answer.

### Version-sensitive

Questions referring to a particular academic year or semester.

------------------------------------------------------------------------

# 17. NO-ANSWER POLICY

The system must distinguish:

``` text
Answer found
```

from:

``` text
No sufficient evidence found
```

Never convert retrieval failure into an invented answer.

Recommended behavior:

``` text
Retrieve
  ↓
Evidence Score / Relevance Assessment
  ↓
Sufficient?
 ┌───────┴───────┐
Yes              No
 ↓                ↓
Generate       Controlled
Answer         No-answer
```

The exact threshold must be determined experimentally.

------------------------------------------------------------------------

# 18. MULTI-DOCUMENT REASONING

If an answer requires multiple documents:

``` text
Document A
+
Document B
+
Document C
      ↓
Evidence Set
      ↓
LLM
      ↓
Combined Answer
      ↓
Multiple Citations
```

The system must retain which evidence supports which portion of the
response.

------------------------------------------------------------------------

# 19. VERSION AWARENESS

Academic information may vary by:

-   Academic year
-   Semester
-   Regulation
-   Document version
-   Publication date

When the query specifies a period, retrieval should use available
metadata to avoid irrelevant versions.

Do not invent document freshness information.

------------------------------------------------------------------------

# 20. EVALUATION-FIRST DEVELOPMENT

Every retrieval enhancement should be evaluated.

Example:

``` text
Baseline Vector RAG
        ↓
Measure
        ↓
Hybrid RAG
        ↓
Measure
        ↓
Hybrid + Re-ranking
        ↓
Measure
        ↓
Grounding Validation
        ↓
Measure
```

Store experiment configurations and results.

Do not overwrite previous experiment results.

------------------------------------------------------------------------

# 21. REPRODUCIBILITY

Experiments should record, where applicable:

``` text
dataset version
document set
chunking configuration
embedding model
vector store configuration
BM25 configuration
fusion method
metadata filters
re-ranker
top_k
LLM
prompt version
evaluation configuration
timestamp
```

The same configuration should be reproducible.

------------------------------------------------------------------------

# 22. CODE QUALITY RULES

Prefer:

-   Small modules
-   Clear interfaces
-   Typed data models where useful
-   Dependency injection where useful
-   Deterministic behavior where possible
-   Testable components
-   Explicit configuration
-   Clear error handling

Avoid:

-   Giant single files
-   Hidden global state
-   Hard-coded paths
-   Hard-coded university facts
-   Hard-coded answers
-   Duplicated retrieval logic
-   Untracked configuration
-   Silent exception swallowing

------------------------------------------------------------------------

# 23. CONFIGURATION RULES

Do not hard-code:

-   Model names
-   API keys
-   Database paths
-   Chunk sizes
-   Top-K
-   Retrieval weights
-   URLs
-   Environment-specific paths

Use configuration/environment variables where appropriate.

Never commit secrets.

------------------------------------------------------------------------

# 24. TESTING RULES

Every major component should have tests.

At minimum:

``` text
Document Loader Tests
Processing Tests
Chunking Tests
Metadata Tests
Embedding Tests
Vector Retrieval Tests
BM25 Tests
Fusion Tests
Filtering Tests
Re-ranking Tests
Context Builder Tests
Generation Tests
Citation Tests
Grounding Tests
API Tests
End-to-End Tests
```

Tests should include failure cases, not only successful cases.

------------------------------------------------------------------------

# 25. FAILURE HANDLING

Failures must remain explicit.

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

Do not silently catch exceptions and continue with invalid state.

------------------------------------------------------------------------

# 26. OBSERVABILITY

The system should make it possible to inspect:

``` text
request_id
query
retrieval strategy
retrieved chunks
document IDs
re-ranking results
latency
LLM model
citation count
validation result
errors
```

Logging must be useful without unnecessarily exposing sensitive
information.

------------------------------------------------------------------------

# 27. PERFORMANCE

Track:

``` text
Query Processing Latency
+
Retrieval Latency
+
Re-ranking Latency
+
Context Construction Latency
+
LLM Generation Latency
+
Validation Latency
=
Total Latency
```

Do not optimize prematurely.

Measure first.

------------------------------------------------------------------------

# 28. SECURITY

The knowledge base should prioritize trusted institutional documents.

Consider:

-   Source validation
-   File validation
-   Upload restrictions
-   Prompt injection resistance
-   Untrusted content handling
-   Metadata integrity
-   Access controls
-   Audit logs

User-provided text must not automatically become authoritative
university evidence.

------------------------------------------------------------------------

# 29. EXTENSIBILITY

The framework must be capable of expanding beyond one department.

Conceptually:

``` text
SRU Assistant
      │
      ├── CSE
      ├── ECE
      ├── EEE
      └── Additional Departments
```

Do not hard-code:

``` text
if department == "CSE":
```

throughout the application.

Use metadata and configuration-driven behavior.

------------------------------------------------------------------------

# 30. DOCUMENT TYPES

The framework should be able to support, as applicable:

-   Academic calendars
-   Examination schedules
-   Course structures
-   Syllabi
-   Examination guidelines
-   Department notices
-   Other official academic documents

The system should be extensible to new document types.

------------------------------------------------------------------------

# 31. UI REQUIREMENTS

The initial UI should prioritize clarity.

Minimum:

``` text
SRU ASSISTANT

[ Ask your academic question... ]

[ Ask ]

Answer:
...

Sources:
...
```

The user should be able to distinguish:

``` text
Generated Answer
```

from:

``` text
Supporting Sources
```

Do not hide citations behind unnecessary UI complexity.

------------------------------------------------------------------------

# 32. API DESIGN

The backend should expose clean boundaries between:

``` text
Query API
Retrieval Service
Generation Service
Citation Service
Document Ingestion Service
Evaluation Service
```

Avoid allowing the frontend to directly manipulate internal
retrieval/database structures.

------------------------------------------------------------------------

# 33. RECOMMENDED PROJECT STRUCTURE

``` text
sru-assistant/
│
├── app/
│   ├── api/
│   ├── services/
│   └── config/
│
├── ingestion/
│   ├── loaders/
│   ├── processors/
│   ├── chunking/
│   └── metadata/
│
├── retrieval/
│   ├── embeddings/
│   ├── vectorstore/
│   ├── lexical/
│   ├── fusion/
│   ├── filtering/
│   └── reranking/
│
├── generation/
│   ├── prompts/
│   ├── llm/
│   └── response/
│
├── citations/
│
├── evaluation/
│   ├── datasets/
│   ├── retrieval/
│   ├── generation/
│   └── reports/
│
├── documents/
│
├── tests/
│
├── frontend/
│
├── scripts/
│
├── configs/
│
├── framework.md
├── RAG.md
├── roadmap.md
├── agent.md
└── README.md
```

The exact structure may evolve if there is a clear engineering reason.

------------------------------------------------------------------------

# 34. IMPLEMENTATION DISCIPLINE

Before writing code:

1.  Identify the current roadmap phase.
2.  Read the relevant framework/RAG requirements.
3.  Inspect existing code.
4.  Identify interfaces affected.
5.  Implement the smallest coherent change.
6.  Add tests.
7.  Run tests.
8.  Run static checks where configured.
9.  Validate behavior.
10. Update documentation if architecture changed.
11. Report what was completed.
12. Identify the next phase.

Do not skip directly to advanced features.

------------------------------------------------------------------------

# 35. CHANGE DISCIPLINE

Before changing an existing architecture:

``` text
What problem does this change solve?
        ↓
Which requirement requires it?
        ↓
Does it affect another module?
        ↓
What tests need updating?
        ↓
Does documentation need updating?
```

Do not make broad refactors without a clear reason.

------------------------------------------------------------------------

# 36. ANTI-DRIFT RULES

Codex must NOT:

-   Turn SRU Assistant into a general-purpose chatbot.
-   Turn SRU Assistant into an autonomous agent framework.
-   Import RYU architecture.
-   Add unnecessary multi-agent systems.
-   Hard-code university answers.
-   Use the LLM as the primary source.
-   Remove citations to simplify implementation.
-   Remove provenance.
-   Skip evaluation.
-   Claim improvements without measurement.
-   Add advanced RAG features before the baseline is stable.
-   Replace official source documents with fabricated data.
-   Silently ignore failed retrieval.
-   Silently swallow errors.
-   Overwrite benchmark results without preserving history.

------------------------------------------------------------------------

# 37. WHEN INFORMATION IS MISSING

If an implementation detail is not defined:

1.  Prefer the simplest design consistent with the documented
    architecture.
2.  Make the decision configurable if it is likely to change.
3.  Document the decision.
4.  Do not invent institutional requirements.
5.  Do not introduce unrelated architecture.

Examples of decisions that may initially remain implementation choices:

-   Exact embedding model
-   Exact vector database
-   Exact LLM
-   Exact chunk size
-   Exact overlap
-   Exact BM25 implementation
-   Exact re-ranking model
-   Exact frontend framework

These should be selected and evaluated during implementation.

------------------------------------------------------------------------

# 38. EXPERIMENT RULE

If a component is uncertain:

``` text
Do not assume.
Build a baseline.
Measure.
Compare.
Choose.
Document.
```

Examples:

``` text
Embedding Model A vs B
Chunk Size A vs B
Vector Only vs Hybrid
RRF vs Weighted Fusion
Re-ranking vs No Re-ranking
Top-K 3 vs 5 vs 10
```

------------------------------------------------------------------------

# 39. DEMONSTRATION REQUIREMENTS

The final system should demonstrate:

### Demo 1 --- Direct Question

``` text
Question
 ↓
Retrieval
 ↓
Answer
 ↓
Citation
```

### Demo 2 --- Exact Identifier

Demonstrate lexical retrieval using a course code or exact academic
identifier.

### Demo 3 --- Paraphrased Query

Demonstrate semantic retrieval.

### Demo 4 --- Multi-Document Question

Demonstrate synthesis across multiple sources.

### Demo 5 --- Unsupported Question

Demonstrate no-answer behavior.

### Demo 6 --- Citation Trace

Show the source document and supporting location.

------------------------------------------------------------------------

# 40. DEFINITION OF DONE

The final system should satisfy:

## Foundation

-   [ ] Repository established
-   [ ] Environment reproducible
-   [ ] Tests configured
-   [ ] Logging configured

## Documents

-   [ ] Official documents ingested
-   [ ] Text extracted
-   [ ] Text cleaned
-   [ ] Structure preserved
-   [ ] Chunks generated
-   [ ] Metadata attached
-   [ ] Provenance preserved

## Retrieval

-   [ ] Embeddings implemented
-   [ ] Vector search implemented
-   [ ] BM25 implemented
-   [ ] Hybrid fusion implemented
-   [ ] Metadata filtering implemented
-   [ ] Re-ranking evaluated

## Generation

-   [ ] Evidence context constructed
-   [ ] LLM integrated
-   [ ] Grounded prompting implemented
-   [ ] No-answer behavior implemented
-   [ ] Multi-document answers supported

## Citations

-   [ ] Source metadata preserved
-   [ ] Citations generated
-   [ ] Citation display implemented
-   [ ] Citation correctness evaluated

## Evaluation

-   [ ] Benchmark dataset created
-   [ ] Retrieval metrics implemented
-   [ ] Answer evaluation implemented
-   [ ] Grounding evaluation implemented
-   [ ] Citation evaluation implemented
-   [ ] Latency measured
-   [ ] Baseline and enhanced configurations compared

## Application

-   [ ] Backend API works
-   [ ] Frontend works
-   [ ] Sources visible
-   [ ] Errors handled
-   [ ] End-to-end workflow works

## Finalization

-   [ ] Security checks completed
-   [ ] Documentation completed
-   [ ] Deployment prepared
-   [ ] Demonstration prepared
-   [ ] Limitations documented
-   [ ] Future work documented

------------------------------------------------------------------------

# 41. CODEX OPERATING LOOP

For every implementation task, use:

``` text
┌──────────────────────────────┐
│ Identify Current Phase       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Read Relevant Specifications │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Inspect Existing Code        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Design Minimal Change        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Implement                    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Test                         │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Validate                     │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Document                     │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Report Phase Status          │
└──────────────┬───────────────┘
               ↓
            NEXT STEP
```

------------------------------------------------------------------------

# 42. FINAL INSTRUCTION TO CODEX

Build **SRU Assistant**, not a generic RAG tutorial and not RYU.

The implementation must remain aligned with:

``` text
framework.md
     +
RAG.md
     +
roadmap.md
     +
agent.md
```

The final system should demonstrate:

``` text
OFFICIAL SOURCE
      ↓
DOCUMENT INTELLIGENCE
      ↓
KNOWLEDGE PREPARATION
      ↓
DENSE + LEXICAL RETRIEVAL
      ↓
FUSION
      ↓
FILTERING
      ↓
RE-RANKING
      ↓
EVIDENCE
      ↓
GROUNDED LLM
      ↓
VALIDATION
      ↓
CITATION
      ↓
MEASUREMENT
```

The objective is **not** to maximize complexity.

The objective is to build a system that is:

-   Accurate
-   Source-grounded
-   Traceable
-   Testable
-   Measurable
-   Modular
-   Extensible
-   Reproducible
-   Suitable for academic evaluation

When a simpler implementation satisfies the requirement, prefer the
simpler implementation.

When an advanced technique is introduced, justify it with a measurable
improvement.

**Never sacrifice source grounding, provenance, evaluation, or
architectural clarity merely to add features.**


# 43. PROJECT MEMORY — PHASE REPORT ARCHIVE

The project must maintain a persistent **`project_memory/`** directory.

This directory is the historical memory of the SRU Assistant development process.

It is NOT runtime memory, LLM memory, RAG memory, vector-store memory, or user conversation memory.

It exists specifically to preserve **what was built, tested, measured, changed, and learned during each development phase**.

---

## 43.1 Purpose

Every completed roadmap phase must leave behind a permanent report in:

```text
project_memory/
```

This prevents loss of project history and allows Codex to understand previous implementation decisions without relying only on the current source tree.

The project memory should answer:

```text
What did we build?
Why did we build it?
What changed?
What was tested?
What passed?
What failed?
What decisions were made?
What remains?
```

---

## 43.2 Required Directory Structure

Create:

```text
project_memory/
├── README.md
│
├── phase_00_project_foundation.md
├── phase_01_document_intelligence.md
├── phase_02_knowledge_preparation.md
├── phase_03_embedding_vector_store.md
├── phase_04_baseline_rag.md
├── phase_05_hybrid_retrieval.md
├── phase_06_retrieval_enhancement.md
├── phase_07_grounded_generation.md
├── phase_08_citation_provenance.md
├── phase_09_rag_evaluation.md
├── phase_10_application_layer.md
├── phase_11_reliability_security.md
├── phase_12_advanced_rag_research.md
├── phase_13_final_integration.md
└── phase_14_deployment_demonstration.md
```

Not every file must exist immediately.

Create the report when the corresponding phase is completed.

---

## 43.3 Phase Completion Rule

A roadmap phase is not considered completely finished until:

```text
Implementation
      ↓
Tests
      ↓
Validation
      ↓
Documentation
      ↓
Phase Report
      ↓
Phase Marked Complete
```

The phase report must be created or updated before moving to the next major phase.

---

## 43.4 Required Phase Report Format

Every phase report should contain:

```markdown
# Phase X — <Phase Name>

## Status

COMPLETED / PARTIAL / BLOCKED

## Objective

<What this phase was intended to accomplish>

## Scope

<What was included>

## Implementation

<List of implemented components>

## Files Added

<List>

## Files Modified

<List>

## Architecture Changes

<Describe architectural changes, if any>

## Configuration

<Important configuration values>

## Tests

<Test commands and test results>

## Validation

<How the implementation was manually or automatically validated>

## Metrics

<Relevant measurements>

## Problems Encountered

<Problems and errors>

## Solutions

<How problems were resolved>

## Decisions

<Important technical decisions and their reasoning>

## Known Limitations

<What is intentionally incomplete>

## Remaining Work

<Items carried forward>

## Dependencies for Next Phase

<What the next phase depends on>

## Final Phase Result

<Concise summary of what was achieved>
```

Not every section requires content if genuinely not applicable, but the section should remain present where useful.

---

## 43.5 Evidence Rules

Phase reports must record actual results.

Do NOT write:

```text
Tests passed.
```

without recording what was actually tested.

Prefer:

```text
Tests:
pytest tests/retrieval -q

Result:
42 passed
```

Likewise, do not claim an improvement without measurements.

For experiments, record:

```text
Configuration
Dataset
Metric
Result
Comparison
Conclusion
```

---

## 43.6 Preserve Failed Attempts

Do not erase important failed implementation attempts from project memory.

If a significant approach was abandoned, record:

```text
Attempt
Why it was tried
Observed failure
Root cause
Decision
Replacement approach
```

This is valuable engineering history and prevents Codex from repeating the same mistake.

---

## 43.7 Architecture Decision History

If an important architectural decision is made, record it in the relevant phase report.

Examples:

```text
Why hybrid retrieval was selected
Why a particular embedding model was selected
Why a vector database was selected
Why RRF was selected over weighted fusion
Why a chunking strategy changed
Why a reranker was introduced
Why a technique was rejected
```

Do not rewrite history merely because the architecture later changes.

Record the evolution.

---

## 43.8 Experiment History

Phase 9 and Phase 12 are especially important.

Maintain experiment records such as:

```text
project_memory/
└── experiments/
    ├── retrieval/
    ├── embeddings/
    ├── chunking/
    ├── reranking/
    └── generation/
```

If experiments become numerous, use this structure.

Each experiment should record:

```text
Experiment ID
Date
Objective
Dataset
Configuration
Baseline
Method
Metrics
Results
Conclusion
```

---

## 43.9 Phase Status Tracking

`project_memory/README.md` should maintain the project phase status.

Example:

```markdown
# SRU Assistant Project Memory

| Phase | Status |
|---|---|
| 0 | COMPLETED |
| 1 | COMPLETED |
| 2 | IN PROGRESS |
| 3 | NOT STARTED |
| 4 | NOT STARTED |
...
```

Update this whenever a phase changes status.

---

## 43.10 Current Project State

The project memory README should also contain:

```text
Current Phase:
Current Objective:
Last Completed Phase:
Next Phase:
Current Architecture Version:
Current RAG Version:
Known Blockers:
```

This gives Codex a quick project-state entry point.

---

## 43.11 Codex Memory Protocol

At the beginning of a major implementation task:

```text
Read:
    agent.md
    framework.md
    RAG.md
    roadmap.md
    project_memory/README.md

Then:
    Read the current phase report
    Inspect relevant source code
    Continue from the documented state
```

Do not assume that the source code alone represents the complete project history.

---

## 43.12 After Completing a Phase

Codex must:

1. Run the required tests.
2. Validate the implementation.
3. Record actual results.
4. Record important decisions.
5. Record problems and solutions.
6. Record known limitations.
7. Create/update the corresponding phase report.
8. Update `project_memory/README.md`.
9. Mark the phase status appropriately.
10. Only then proceed to the next phase.

---

## 43.13 If a Phase Is Partially Complete

Do not mark it as completed.

Use:

```text
PARTIAL
```

and record:

```text
Completed:
...

Remaining:
...

Blockers:
...
```

This prevents false project progress.

---

## 43.14 If a Phase Is Blocked

Use:

```text
BLOCKED
```

Record:

```text
Blocker
Impact
What was attempted
What is required to continue
```

Do not silently skip the phase.

---

## 43.15 Relationship to Other Documentation

The responsibilities are:

```text
framework.md
    ↓
What SRU Assistant IS

RAG.md
    ↓
How the RAG system WORKS

roadmap.md
    ↓
What should be BUILT and WHEN

agent.md
    ↓
How Codex MUST BUILD IT

project_memory/
    ↓
What HAS ACTUALLY BEEN BUILT
```

This distinction is mandatory.

`project_memory/` records **actual project history**, not planned architecture.

---

## 43.16 No Fabricated Reports

Codex must never create a phase report claiming work that was not actually performed.

Do not fabricate:

- Test counts
- Coverage
- Retrieval metrics
- Accuracy
- Latency
- Model performance
- Completed features
- Successful deployment
- Evaluation results

If a metric has not been measured:

```text
Not measured yet.
```

If a feature has not been implemented:

```text
Not implemented.
```

---

## 43.17 Memory Is Append-and-Update History

Project memory should preserve historical knowledge.

When a later phase changes an earlier decision:

```text
Old Decision
    ↓
New Evidence
    ↓
New Decision
```

Record the change in the new phase report.

Do not silently rewrite old reports to make the history look cleaner.

---

## 43.18 Mandatory Project Memory Gate

The final project cannot be considered fully documented unless:

```text
Phase 0 report exists
Phase 1 report exists
Phase 2 report exists
...
Phase 14 report exists
```

for every phase that was actually undertaken.

If a phase was skipped by explicit project decision, record the reason in `project_memory/README.md`.

---

# 44. UPDATED CODEX OPERATING LOOP

The implementation loop is now:

```text
┌──────────────────────────────┐
│ Read Project Memory          │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Identify Current Phase       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Read Relevant Specifications │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Inspect Existing Code        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Design Minimal Change        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Implement                    │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Test                         │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Validate                     │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Record Actual Results        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Update project_memory/       │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Update Project Status        │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ Proceed to Next Phase        │
└──────────────────────────────┘
```

**Project memory is mandatory, not optional.**
