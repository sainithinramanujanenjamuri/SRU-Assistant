# SRU Assistant Framework

## 1. Project Identity

**Project Title:** SRU Assistant: A RAG Framework for University
Academic Query Resolution

**Project Type:** Capstone Project

**Domain:** Artificial Intelligence / Natural Language Processing /
Retrieval-Augmented Generation (RAG)

> **Important:** SRU Assistant is a completely independent project. It
> is not part of the RYU AI Framework and does not inherit RYU's
> architecture, terminology, runtime, agents, workers, spaces, or
> autonomous-system design.

------------------------------------------------------------------------

## 2. Problem Statement

Students at SR University need information from multiple institutional
sources such as:

-   Course structures
-   Syllabi
-   Semester calendars
-   Examination schedules
-   Examination guidelines
-   Department notices
-   Other official academic documents

This information can be distributed across different documents and may
be difficult to locate quickly. Students may also rely on outdated PDFs
or word-of-mouth information.

The objective of SRU Assistant is to provide a unified natural-language
interface for retrieving academic information from official university
documents.

------------------------------------------------------------------------

## 3. Core Objective

SRU Assistant will build a **source-grounded academic question-answering
framework**.

Given a student's natural-language query, the framework should:

1.  Understand the query.
2.  Search the university's document knowledge base.
3.  Retrieve the most relevant document segments.
4.  Provide the retrieved context to a Large Language Model.
5.  Generate an answer grounded in the retrieved material.
6.  Cite the source material used for the answer.
7.  Avoid presenting unsupported information as factual.

The system should prioritize **retrieval and evidence** rather than
relying solely on the LLM's pretrained knowledge.

------------------------------------------------------------------------

## 4. Core Principle

The central design principle is:

> **Retrieve first. Generate second. Cite the evidence.**

The LLM should not be treated as the primary source of university
information.

The university's official documents form the knowledge base, while the
LLM acts as the language-generation and reasoning layer over retrieved
evidence.

------------------------------------------------------------------------

## 5. High-Level Architecture

``` text
                    ┌──────────────────────────┐
                    │   SR University Sources  │
                    │                          │
                    │  Syllabi                 │
                    │  Calendars               │
                    │  Exam Schedules          │
                    │  Notices                 │
                    │  Guidelines              │
                    │  Course Structures       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Document Ingestion     │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Text Extraction &        │
                    │ Document Processing       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Chunking & Metadata       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Embedding Generation     │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │    Vector Database       │
                    └────────────┬─────────────┘
                                 │
                                 │
Student Query ──────► Query Processing
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Semantic Retrieval       │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Retrieved Evidence       │
                    │ + Metadata + Citations   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │       LLM Layer          │
                    │ Context-grounded         │
                    │ response generation      │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │ Answer + Source          │
                    │ Citations                 │
                    └──────────────────────────┘
```

------------------------------------------------------------------------

## 6. Framework Layers

### 6.1 Document Layer

Responsible for acquiring and managing university academic documents.

Possible document types include:

-   PDF
-   DOCX
-   Text documents
-   Structured academic data
-   Department notices
-   Academic schedules

Each document should retain useful metadata such as:

``` text
document_id
document_name
document_type
department
academic_year
semester
source
version
ingestion_timestamp
```

The exact metadata schema will be finalized during implementation.

------------------------------------------------------------------------

### 6.2 Ingestion Layer

The ingestion layer converts raw institutional documents into
machine-processable content.

Pipeline:

``` text
Raw Document
     ↓
Validation
     ↓
Text Extraction
     ↓
Cleaning
     ↓
Structure Detection
     ↓
Metadata Assignment
     ↓
Chunk Creation
```

The ingestion pipeline should preserve document provenance so that
retrieved content can later be traced back to the original source.

------------------------------------------------------------------------

### 6.3 Chunking Layer

Large documents should be divided into meaningful sections before
embedding.

A chunk should contain enough surrounding context to represent a
coherent academic fact.

Example:

``` text
Document:
B.Tech CSE Academic Calendar 2026-27

Chunk:
Mid-Semester Examination I:
12 September 2026 – 16 September 2026
```

Metadata should remain attached to the chunk:

``` text
chunk_id
document_id
page_number
section
department
semester
academic_year
source
```

Chunking strategy will be evaluated experimentally rather than assumed
to be optimal.

------------------------------------------------------------------------

### 6.4 Embedding Layer

Each document chunk is converted into a vector representation.

``` text
Text Chunk
    ↓
Embedding Model
    ↓
Dense Vector
    ↓
Vector Database
```

The embedding model should represent the semantic meaning of academic
content so that conceptually similar queries can retrieve relevant
passages even when the query does not use the exact wording found in the
source document.

------------------------------------------------------------------------

### 6.5 Vector Storage Layer

The vector database stores:

-   Embeddings
-   Original text chunks
-   Document identifiers
-   Metadata
-   Source information
-   Citation information

Conceptually:

``` text
Vector
+
Chunk Text
+
Metadata
+
Provenance
```

The vector database technology will be selected based on the final
implementation requirements.

------------------------------------------------------------------------

## 7. Query Processing Pipeline

When a student asks a question:

``` text
User Query
    ↓
Query Normalization
    ↓
Query Embedding
    ↓
Vector Search
    ↓
Candidate Documents
    ↓
Relevance Filtering / Ranking
    ↓
Evidence Context
    ↓
LLM
    ↓
Grounded Answer
    ↓
Citation Construction
    ↓
Final Response
```

Example query:

> "When are the CSE mid-semester examinations?"

The system should retrieve relevant academic-calendar or
examination-schedule content rather than asking the LLM to recall the
answer from its pretrained knowledge.

------------------------------------------------------------------------

## 8. Retrieval Layer

Retrieval is a critical part of the framework.

The retrieval subsystem should determine:

-   Which documents are relevant?
-   Which chunks contain the answer?
-   How many chunks should be passed to the LLM?
-   How should relevance be ranked?
-   How should irrelevant evidence be filtered?

The initial framework can use semantic vector retrieval.

Later versions may evaluate:

``` text
Dense Retrieval
       +
Metadata Filtering
       +
Re-ranking
       +
Keyword / Lexical Retrieval
```

A hybrid retrieval strategy may be introduced if evaluation shows that
semantic retrieval alone is insufficient for academic queries containing
exact course codes, dates, regulations, or names.

------------------------------------------------------------------------

## 9. Evidence Context

Retrieved information should be assembled into a controlled context for
the LLM.

Example:

``` text
SYSTEM:
Answer using only the supplied university evidence.

EVIDENCE:

[Source 1]
Document: Academic Calendar 2026-27
Page: 3
Content:
...

[Source 2]
Document: Examination Schedule
Page: 2
Content:
...

USER QUERY:
When are the CSE mid-semester examinations?
```

This creates an explicit separation between:

-   User question
-   Retrieved evidence
-   Generated answer

------------------------------------------------------------------------

## 10. LLM Generation Layer

The LLM receives the user query together with retrieved evidence.

Its responsibility is to:

-   Interpret the question.
-   Synthesize information from retrieved evidence.
-   Produce a natural-language response.
-   Avoid unsupported claims.
-   Preserve important dates, names, codes, and constraints.
-   Associate statements with their supporting sources.

The LLM should not be allowed to freely answer university-specific
questions without retrieved evidence.

------------------------------------------------------------------------

## 11. Grounding Policy

The framework should enforce a grounding policy.

### Rule 1 --- Evidence First

University-specific factual claims should be based on retrieved
institutional content.

### Rule 2 --- No Evidence, No Fabrication

If sufficient evidence cannot be retrieved, the system should not invent
an answer.

Example:

> "I couldn't find sufficient information in the available SR University
> documents to answer this accurately."

### Rule 3 --- Source Traceability

Every grounded response should expose the source document or relevant
citation information.

### Rule 4 --- Preserve Uncertainty

If retrieved documents contain incomplete or conflicting information,
the system should indicate this rather than silently selecting
unsupported information.

------------------------------------------------------------------------

## 12. Citation Layer

Citations are a core feature rather than an optional UI element.

A citation should allow the user to understand where the answer came
from.

Possible citation information:

``` text
Source:
Academic Calendar 2026-27
Page: 3
Section: Examination Schedule
```

The exact citation format will be defined during implementation.

The framework should preserve provenance from:

``` text
Original Document
      ↓
Document Chunk
      ↓
Retrieved Evidence
      ↓
Generated Answer
      ↓
Citation
```

------------------------------------------------------------------------

## 13. Response Architecture

A final response may follow this structure:

``` text
Answer

The CSE Mid-Semester Examination I is scheduled
for 12 September 2026 to 16 September 2026.

Sources:
• Academic Calendar 2026-27 — Page 3
```

The UI should make the distinction between the generated answer and its
supporting evidence clear.

------------------------------------------------------------------------

## 14. Knowledge Base Management

The framework should support adding new university documents without
redesigning the entire application.

``` text
New Document
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

This is important because academic information changes over time.

The framework should therefore be designed around **replaceable and
updateable knowledge**, rather than embedding information directly into
application code.

------------------------------------------------------------------------

## 15. Document Version Awareness

University documents may be updated or replaced.

The system should therefore consider:

-   Academic year
-   Semester
-   Publication date
-   Version
-   Document status
-   Ingestion timestamp

The framework should avoid treating every document as equally current.

A later implementation can introduce explicit document-version
resolution when sufficient institutional metadata is available.

------------------------------------------------------------------------

## 16. Department Extensibility

The approved project is intended to be extensible to additional
departments and document types.

Conceptually:

``` text
                 SRU Assistant
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
      CSE            ECE            EEE
       │              │              │
   Documents      Documents      Documents
```

The architecture should therefore avoid hard-coded CSE-only logic.

------------------------------------------------------------------------

## 17. Initial Technology Architecture

The exact technology stack is not fixed by the approval form and should
be selected during implementation.

The framework will require components for:

``` text
Frontend
Backend/API
Document Processing
Embedding Model
Vector Database
LLM
Retrieval Engine
Citation/Provenance System
Evaluation System
```

Technology choices should be made based on:

-   Local execution requirements
-   Accuracy
-   Resource requirements
-   Ease of development
-   Reproducibility
-   Deployment requirements
-   Evaluation results

------------------------------------------------------------------------

## 18. Evaluation Framework

A major objective should be to demonstrate that SRU Assistant is not
merely a chatbot interface.

Evaluation should measure at least:

### Retrieval Quality

Whether the correct document chunks are retrieved.

Possible metrics:

-   Recall@K
-   Precision@K
-   MRR
-   nDCG

### Answer Quality

Whether the generated response correctly answers the question.

Possible evaluation dimensions:

-   Correctness
-   Relevance
-   Completeness
-   Groundedness

### Citation Quality

Whether cited sources actually support the generated claims.

### Hallucination / Unsupported Claim Rate

Measure how frequently the system produces claims that cannot be
supported by the retrieved university evidence.

### Latency

Measure:

``` text
Query
 ↓
Retrieval time
 ↓
Generation time
 ↓
Total response time
```

------------------------------------------------------------------------

## 19. Test Query Dataset

A dedicated evaluation dataset should be created from actual university
documents.

Example categories:

``` text
1. Direct factual questions
2. Date-based questions
3. Course-related questions
4. Regulation questions
5. Multi-document questions
6. Department-specific questions
7. Ambiguous questions
8. Questions with no answer in the knowledge base
9. Outdated-information cases
10. Paraphrased questions
```

Each evaluation question should have a ground-truth reference where
possible.

------------------------------------------------------------------------

## 20. Failure Handling

The framework should explicitly handle retrieval and generation
failures.

### No Relevant Document

``` text
Query
 ↓
Retrieval
 ↓
No sufficient evidence
 ↓
Grounding failure response
```

### Low-Confidence Retrieval

The system should avoid generating a confident answer when retrieval
quality is insufficient.

### Conflicting Documents

The system should surface the conflict and identify the relevant sources
rather than silently merging contradictory information.

### Unsupported Question

If the question is outside the available academic knowledge base, the
system should state that the required information was not found.

------------------------------------------------------------------------

## 21. Security and Data Integrity

Because the framework uses institutional documents, document integrity
and access control should be considered.

The system should distinguish between:

``` text
Trusted Institutional Source
        ↓
Knowledge Base
        ↓
Retrieval
        ↓
Answer
```

and arbitrary user-provided content.

Future implementation may include:

-   Document validation
-   Source whitelisting
-   File integrity checks
-   Access control
-   Upload restrictions
-   Audit logs

These features should be introduced according to the actual deployment
requirements.

------------------------------------------------------------------------

## 22. Proposed Repository Structure

Initial structure:

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
│   ├── search/
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
├── requirements.txt
│
└── README.md
```

This is a starting architecture and should evolve as implementation
decisions are validated.

------------------------------------------------------------------------

## 23. Development Philosophy

SRU Assistant should be developed as a **framework**, not simply as a
one-off chatbot.

The system should have clear boundaries between:

``` text
Documents
   ↓
Ingestion
   ↓
Knowledge Representation
   ↓
Retrieval
   ↓
Evidence
   ↓
Generation
   ↓
Citations
   ↓
Evaluation
```

Each component should be independently testable.

------------------------------------------------------------------------

## 24. Core Research Question

A central research direction for the project is:

> **How effectively can a RAG-based framework provide accurate,
> source-grounded answers to university academic queries using
> institutional documents?**

The implementation and evaluation should provide measurable evidence
rather than relying only on demonstrations.

------------------------------------------------------------------------

## 25. Future Extensions

Potential extensions include:

-   Hybrid retrieval
-   Cross-encoder re-ranking
-   Query rewriting
-   Multi-query retrieval
-   Metadata-aware retrieval
-   Document version resolution
-   Multilingual academic queries
-   Conversation-aware retrieval
-   Structured academic data integration
-   Administrative query support
-   Department-specific knowledge spaces
-   Analytics for frequently asked questions
-   Feedback-driven retrieval improvement

These are future directions and are not assumed to be part of the
initial implementation.

------------------------------------------------------------------------

## 26. Definition of Done --- Initial Framework

The first complete version of SRU Assistant should be able to:

-   [ ] Ingest official academic documents.
-   [ ] Extract and process document content.
-   [ ] Split documents into retrievable chunks.
-   [ ] Generate embeddings.
-   [ ] Store chunks and embeddings in a vector database.
-   [ ] Accept natural-language student queries.
-   [ ] Retrieve relevant evidence.
-   [ ] Generate answers using retrieved context.
-   [ ] Provide source citations.
-   [ ] Refuse or qualify answers when sufficient evidence is
    unavailable.
-   [ ] Evaluate retrieval quality.
-   [ ] Evaluate answer grounding and correctness.
-   [ ] Provide a usable student-facing interface.
-   [ ] Support adding additional departments/documents.

------------------------------------------------------------------------

## 27. Project Boundary

### In Scope

-   University academic documents
-   RAG pipeline
-   Semantic retrieval
-   LLM-based answer generation
-   Source citations
-   Document provenance
-   Academic query resolution
-   Retrieval and answer evaluation
-   Extensible document architecture

### Not Automatically In Scope

-   General-purpose autonomous agents
-   Autonomous software development
-   General-purpose AGI
-   Game development automation
-   RYU AI Runtime
-   RYU Spaces
-   RYU Workers
-   Autonomous research systems
-   General internet search as the primary knowledge source

The project should remain focused on university academic query
resolution.

------------------------------------------------------------------------

## 28. Architectural Principle

The framework can be summarized as:

``` text
OFFICIAL UNIVERSITY KNOWLEDGE
            ↓
      STRUCTURED EVIDENCE
            ↓
        RETRIEVAL
            ↓
      CONTEXT-GROUNDED LLM
            ↓
       TRACEABLE ANSWER
```

**SRU Assistant is fundamentally an evidence-retrieval and
grounded-generation system for university academic information.**
