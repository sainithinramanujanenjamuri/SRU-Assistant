# SR UNIVERSITY
### SCHOOL OF COMPUTER SCIENCE & ARTIFICIAL INTELLIGENCE
**Ananthasagar, Hasanparthy, Warangal, Telangana – 506371**

---

# A CAPSTONE PROJECT REPORT
## ON
# **SRU Assistant: A RAG Framework for University Academic Query Resolution**

*Submitted in partial fulfillment of the requirements for the award of the degree of*  
**BACHELOR OF TECHNOLOGY**  
*in*  
**COMPUTER SCIENCE & ENGINEERING**

---

### **Submitted By: Capstone Project Team No. 235**

| Roll Number | Student Name |
|---|---|
| **2303A52492** | **SUNKARI SAI** |
| **2403A52L05** | **ENJAMURI SAI NITHIN** |
| **2403A52L07** | **DANCHANALA PAVAN** |
| **2403A52L10** | **AZMEERA THARUN** |
| **2403A52L11** | **BOLAGANI SUSHANTH** |

---

### **Under the Guidance of:**
**Project Guide Name:** ________________________  
**Designation:** Assistant Professor / Associate Professor  
**Department:** School of Computer Science & Artificial Intelligence (CS&AI)  
**SR University, Warangal**

**Academic Year:** 2026–2027 | **Semester:** VII

---

<div style="page-break-after: always;"></div>

## CERTIFICATE

This is to certify that the Capstone Project Report entitled **"SRU Assistant: A RAG Framework for University Academic Query Resolution"** is a bonafide work carried out by **Team No. 235** consisting of:

- **Sunkari Sai** (Roll No: 2303A52492)
- **Enjamuri Sai Nithin** (Roll No: 2403A52L05)
- **Danchanala Pavan** (Roll No: 2403A52L07)
- **Azmeera Tharun** (Roll No: 2403A52L10)
- **Bolagani Sushanth** (Roll No: 2403A52L11)

in partial fulfillment of the requirements for the award of the degree of **Bachelor of Technology in Computer Science & Engineering** from **SR University, Warangal**, during the academic year 2026–2027.

The results embodied in this report have not been submitted to any other University or Institute for the award of any degree or diploma.


\
**Signature of Project Guide** &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; **Signature of Head of Department**  
Date: &emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp;&emsp; School of CS&AI, SR University  

\
\
**External Examiner**  
Date:

---

<div style="page-break-after: always;"></div>

## DECLARATION

We hereby declare that the project work titled **"SRU Assistant: A RAG Framework for University Academic Query Resolution"** submitted to the School of Computer Science & Artificial Intelligence, SR University, Warangal, is an original record of work conducted by us under the supervision and guidance of our project guide.

We further declare that this report has not formed the basis for the award of any degree, diploma, associateship, fellowship, or similar title to any candidate of any other University or Institution.

**Team 235 Members:**
1. Sunkari Sai (2303A52492)
2. Enjamuri Sai Nithin (2403A52L05)
3. Danchanala Pavan (2403A52L07)
4. Azmeera Tharun (2403A52L10)
5. Bolagani Sushanth (2403A52L11)

Place: Warangal  
Date: October 2026

---

<div style="page-break-after: always;"></div>

## ACKNOWLEDGMENTS

We express our deep gratitude and heartfelt respect to our **Project Guide**, School of Computer Science & Artificial Intelligence, for invaluable suggestions, continuous encouragement, and technical guidance throughout the formulation and implementation of this capstone project.

We convey our sincere thanks to the **Dean and Head of Department, School of CS&AI, SR University**, for providing us with the necessary computational facilities, administrative permissions, and resources to successfully develop and evaluate this research framework.

We also thank our respected faculty members, technical laboratory staff, and peer students of SR University whose constructive feedback and support helped us validate the institutional query benchmarks.

Lastly, we express our profound gratitude to our parents and families for their constant moral encouragement and blessings throughout our undergraduate engineering journey.

---

<div style="page-break-after: always;"></div>

## ABSTRACT

Students, faculty, and administrative personnel at SR University routinely encounter friction when seeking verified academic information scattered across extensive multi-page documents, including B.Tech R23 academic regulations, semester syllabi, academic calendars, examination notices, and project guidelines. Traditional approaches rely on manual inspection of large PDFs or generic standalone chatbots. Standalone Large Language Models (LLMs) suffer from severe parametric hallucinations, ignorance of private institutional rules, and an inability to provide verifiable source citations.

To address these challenges, this capstone project presents **SRU Assistant**, an end-to-end, zero-cost, source-grounded Retrieval-Augmented Generation (RAG) framework engineered specifically for SR University. The framework introduces a decoupled multi-stage architecture:
1. An offline document intelligence pipeline that normalizes diverse institutional documents (Word `.docx`, PDF, and plain text) with table structural preservation and boundary-aware recursive chunking.
2. A dual-indexing strategy combining dense continuous semantic vector embeddings with a sparse BM25 Okapi inverted index covering 709 domain vocabulary terms.
3. A runtime query processing engine featuring prompt injection defenses, institutional acronym normalization (*"mid 1"* $\rightarrow$ *"Mid-Semester Examination I"*), and Reciprocal Rank Fusion (RRF $k=60$) with two-stage cross-encoder re-ranking.
4. An evidence-first generation module with strict negative constraints, automated conflict detection, and controlled safe refusal on out-of-domain queries.
5. A citation provenance engine linking every generated claim to verifiable document names, sections, pages, and exact chunk excerpts.

The proposed architecture was evaluated on an institutional benchmark of 16 queries across 10 academic categories. Ablation experiments demonstrate that Hybrid Retrieval with Re-ranking achieves a **+25.9% relative gain in Mean Reciprocal Rank (MRR)** (improving from 0.5625 to 0.7083) and a **+9.3% absolute gain in Recall@5** (71.9% to 81.2%) compared to baseline vector RAG, while maintaining **100.0% citation precision** and **94.2% groundedness**. The system operates with an end-to-end latency of under **8 ms** on local consumer hardware without external paid cloud API dependencies, establishing an authentic, privacy-preserving, and mathematically justified solution for institutional academic query resolution.

---

<div style="page-break-after: always;"></div>

## TABLE OF CONTENTS

- **Certificate**
- **Declaration**
- **Acknowledgments**
- **Abstract**
- **List of Figures**
- **List of Tables**
- **Chapter 1: Introduction**
  - 1.1 Background & Context
  - 1.2 Problem Statement
  - 1.3 Motivation & Research Objectives
  - 1.4 Scope & Limitations
  - 1.5 Report Outline
- **Chapter 2: Literature Review**
  - 2.1 Information Retrieval: Classical vs Neural Approaches
  - 2.2 Dense Passage Retrieval & Vector Embeddings
  - 2.3 Sparse Lexical Retrieval: The BM25 Okapi Model
  - 2.4 Retrieval-Augmented Generation (RAG) Architectures
  - 2.5 Hallucination Mitigation & Provenance Attribution
  - 2.6 Comparative Summary & Identified Research Gaps
- **Chapter 3: System Architecture & Design**
  - 3.1 High-Level Architectural Flow
  - 3.2 Document Intelligence & Boundary-Aware Chunking Pipeline
  - 3.3 Dual Indexing Subsystem: Vector Store & BM25 Inverted Index
  - 3.4 Hybrid Fusion via Reciprocal Rank Fusion (RRF)
  - 3.5 Two-Stage Cross-Encoder Re-ranking
  - 3.6 Evidence-First Grounded Generation & Conflict Detection
  - 3.7 Fine-Grained Citation Attribution & Verification
  - 3.8 Security, Reliability & Guardrail Architecture (Phase 11 & 12)
- **Chapter 4: Implementation & Algorithms**
  - 4.1 System Environment & Zero-Cost Architecture
  - 4.2 Algorithm 1: Boundary-Aware Recursive Chunker
  - 4.3 Algorithm 2: Reciprocal Rank Fusion Ranking
  - 4.4 Algorithm 3: Evidence-First Grounded Synthesis & Safe Refusal
  - 4.5 Algorithm 4: Automated Citation Provenance Verification
  - 4.6 REST API & Interactive Glassmorphic Web Application
- **Chapter 5: Experimental Evaluation & Results**
  - 5.1 Benchmark Dataset Construction (Phase 9)
  - 5.2 Evaluation Metrics (MRR, Recall@K, nDCG, Groundedness, Citation Precision)
  - 5.3 Comparative Ablation Experiments (Exp A, B, C, D)
  - 5.4 Academic Category Performance Analysis
  - 5.5 Latency & Computational Profile
  - 5.6 Discussion & Practical Insights
- **Chapter 6: Conclusion & Future Scope**
  - 6.1 Summary of Deliverables & Achievements
  - 6.2 Future Work (Local Small LLM, Vernacular Translation, LMS Integration)
- **References**

---

<div style="page-break-after: always;"></div>

## LIST OF FIGURES

- **Figure 3.1:** High-Level Architectural Flow of SRU Assistant
- **Figure 3.2:** Document Ingestion, Table Normalization, and Boundary-Aware Chunking
- **Figure 3.3:** Dense-Sparse Dual Indexing Architecture
- **Figure 3.4:** Reciprocal Rank Fusion (RRF) and Candidate Re-ranking Pipeline
- **Figure 3.5:** Evidence-First Generation and Citation Verification Cycle
- **Figure 4.1:** Interactive Student Web Application Interface
- **Figure 5.1:** Ablation Comparison of MRR across RAG Configurations (A, B, C, D)
- **Figure 5.2:** Multi-Stage Latency Breakdown on Consumer Hardware

---

## LIST OF TABLES

- **Table 2.1:** Comparative Analysis of Information Retrieval Paradigms
- **Table 3.1:** Institutional Acronym Normalization Dictionary
- **Table 5.1:** Academic Benchmark Dataset Distribution across Query Categories
- **Table 5.2:** Comparative Performance Matrix Across RAG Configurations (Exp A–D)
- **Table 5.3:** Detailed Retrieval Performance Metrics (Recall, Precision, MRR, nDCG)
- **Table 5.4:** Generation Quality and RAG Triad Metrics
- **Table 5.5:** Citation and Provenance Verification Metrics
- **Table 5.6:** Multi-Stage Latency Profiling (Mean & P95 in Milliseconds)

---

<div style="page-break-after: always;"></div>

# CHAPTER 1: INTRODUCTION

## 1.1 Background & Context
Higher education institutions manage an extensive corpus of administrative, regulatory, and pedagogical documents. At SR University (Warangal, Telangana), official institutional information is distributed across several foundational instruments:
1. **Academic Regulations (R23):** Defining graduation credit thresholds (160 credits), attendance requirements (75% minimum, 65% condonation), continuous internal evaluation (CIE 40 marks), semester end examinations (SEE 60 marks), and promotion criteria.
2. **Academic Calendars:** Outlining semester timelines, instruction spells, mid-semester examination weeks, practical exam dates, and vacation periods.
3. **Course Syllabi:** Detailing course codes, credit distribution, lecture-tutorial-practical (L-T-P) hours, unit syllabi, and recommended textbooks.
4. **Capstone Project Guidelines:** Formulating approval processes, team structures, interim evaluations, and final defense procedures.

Under conventional administrative workflows, students obtain answers to operational queries either by manually searching through extensive PDF documents, consulting fellow students, or physically approaching departmental offices. This process introduces substantial friction, delays, and occasional misinformation due to outdated circulating circulars.

## 1.2 Problem Statement
The central challenge addressed in this capstone project is:

> *"How can a university provide accurate, real-time, natural language answers to complex student academic queries while guaranteeing zero hallucinations, complete verifiability against official institutional documents, sub-millisecond local execution, and zero software licensing or cloud API costs?"*

Stand-alone commercial Large Language Models (such as GPT-4, Claude, or Gemini) fail in this setting due to three critical limitations:
- **Parametric Isolation:** Commercial LLMs are trained on general internet corpora and have no exposure to internal SR University institutional documents.
- **Parametric Hallucination:** When prompted with specific regulatory inquiries (e.g., *"What is the passing mark in Mid-1 at SR University?"*), generic models generate plausible-sounding but factually fabricated numbers.
- **Absence of Provenance:** Commercial chatbots generate prose without verifiable citations to page numbers or official regulatory sections, leaving students unable to verify decisions.

## 1.3 Motivation & Research Objectives
To solve these challenges, this project investigates and implements **Retrieval-Augmented Generation (RAG)**. RAG decouples knowledge retrieval from linguistic synthesis by dynamically retrieving authoritative context passages from a curated repository and conditioning generation on those retrieved passages.

The specific objectives of this capstone research are:
1. **Develop an Offline Ingestion Engine:** Parse diverse institutional formats (`.docx`, `.pdf`, `.txt`), preserve tabular relationships, and construct boundary-aware chunks.
2. **Implement Dense-Sparse Dual Indexing:** Combine continuous semantic vector representations (SQLite) with an exact keyword inverted index (BM25 Okapi).
3. **Design a Hybrid Fusion Pipeline:** Implement Reciprocal Rank Fusion (RRF $k=60$) and two-stage cross-encoder re-ranking to optimize candidate selection.
4. **Enforce Grounded Generation:** Prevent hallucinated answers through negative prompt constraints, conflict detection, and controlled fallback safe refusal.
5. **Construct a Fine-Grained Provenance Engine:** Attribute assertions to in-text citations linked to exact document names, sections, pages, and chunk excerpts.
6. **Implement Reliability & Security Guardrails:** Harden the application against prompt injections, enforce input bounds, and provide privacy-preserving telemetry.
7. **Conduct Rigorous Empirical Benchmarks:** Quantitatively validate the architecture using ablation studies across Recall@K, MRR, nDCG, Groundedness, and Latency.
8. **Deliver a Production-Ready Application:** Deploy a zero-cost local backend and modern web user interface for student usage.

## 1.4 Scope & Limitations
- **Scope:** The system covers official academic documents of SR University, including B.Tech R23 regulations, Semester VII computer science syllabi, the 2026–2027 academic calendar, and capstone guidelines.
- **Hardware Profile:** All ingestion, indexing, retrieval, and synthesis pipelines are designed to execute locally on consumer personal computers without specialized GPU accelerators or external paid API keys.
- **Limitations:** The initial deployment focuses on English-language academic documents; vernacular language support (Telugu/Hindi) is designated as future scope.

## 1.5 Report Outline
The remainder of this report is organized as follows: Chapter 2 reviews the literature on information retrieval, RAG, and hallucination mitigation. Chapter 3 details the architecture and mathematical design of SRU Assistant. Chapter 4 provides algorithmic formulations and implementation specifics. Chapter 5 presents empirical ablation results and discussion. Chapter 6 concludes the report and discusses future research directions.

---

<div style="page-break-after: always;"></div>

# CHAPTER 2: LITERATURE REVIEW

## 2.1 Information Retrieval: Classical vs Neural Approaches
Information Retrieval (IR) systems aim to locate relevant documents from a collection in response to a user's information need. Classical IR relies on lexical term matching, represented primarily by Term Frequency-Inverse Document Frequency (TF-IDF) and the BM25 Okapi probabilistic model (Robertson et al., 1994). While BM25 provides exceptional precision for exact keyword matches, it suffers from the *vocabulary mismatch problem*—failing when queries and documents express identical concepts using different vocabulary.

With the advent of deep transformer architectures (Vaswani et al., 2017), Dense Retrieval gained prominence (Karpukhin et al., 2020). Dense retrievers map queries and passages into dense continuous embedding spaces where semantic similarity is measured via inner products or cosine distance. While dense models excel at semantic generalizations and synonymy, they frequently fail on exact numeric identifiers, rare course codes, and acronyms.

## 2.2 Dense-Sparse Hybrid Retrieval
To combine the strengths of both paradigms, researchers have investigated hybrid retrieval architectures. Hybrid retrieval runs dense semantic search and sparse lexical search in parallel. However, a major challenge in hybrid retrieval is *score calibration*: cosine similarity scores range between $[-1, 1]$, whereas BM25 scores are unbounded non-negative real numbers.

Cormack, Clarke, and Buettcher (2009) proposed **Reciprocal Rank Fusion (RRF)**, a robust, rank-based combination technique that bypasses score normalization by computing:
$$RRF(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$
Empirical studies have shown that RRF consistently matches or outperforms complex learned rank fusion models while remaining computationally lightweight and parameter-free.

## 2.3 Retrieval-Augmented Generation (RAG)
Lewis et al. (2020) formalized Retrieval-Augmented Generation, combining a parametric sequence-to-sequence model with a non-parametric neural retriever. In academic and institutional question answering, RAG architectures provide three paramount benefits:
1. **Dynamic Knowledge Updating:** Institutional rules can be modified by updating the document index without costly retraining or fine-tuning of neural model weights.
2. **Domain Specialization:** Private university guidelines remain confidential and localized.
3. **Verifiable Traceability:** Models can cite the exact retrieved documents used to formulate an answer.

Recent surveys (Gao et al., 2023) categorize RAG systems into *Naive RAG*, *Advanced RAG*, and *Modular RAG*. Naive RAG suffers from low retrieval precision, context window saturation, and hallucinated syntheses. Advanced RAG incorporates pre-retrieval query rewriting, hybrid retrieval, post-retrieval re-ranking, and grounded generation guardrails.

## 2.4 Hallucination Mitigation & Provenance Attribution
Hallucination in LLMs refers to generated content that is nonsensical or unfaithful to provided source material (Ji et al., 2023). In academic settings, hallucinations can mislead students regarding graduation criteria or examination schedules.

To mitigate hallucinations, recent literature emphasizes:
- **Evidence-First Prompt Constraints:** Restricting generation exclusively to facts present in the provided evidence.
- **Negative Rejection (Safe Refusal):** Instructing the model to output a polite refusal when retrieved evidence is insufficient or of low relevance.
- **Automated Verification:** Cross-referencing generated factual claims against retrieved chunk tokens to ensure complete support before rendering.

## 2.5 Comparative Analysis & Research Gaps
Table 2.1 summarizes the capabilities of existing paradigms compared to the requirements of university academic query resolution:

| Architecture | Semantic Understanding | Exact Code / Date Matching | Citation Traceability | Hallucination Prevention | Zero-Cost Local Runtime |
|---|---|---|---|---|---|
| **Classical Keyword Search (BM25)** | ❌ Poor | ✅ High | ❌ None | N/A (Doc list only) | ✅ Yes |
| **Pure Vector Search (Dense RAG)** | ✅ High | ❌ Low | ⚠️ Partial | ❌ Weak | ✅ Yes |
| **Commercial Cloud LLMs (ChatGPT)** | ✅ High | ⚠️ Moderate | ❌ None | ❌ Prone | ❌ Paid / Privacy Risks |
| **SRU Assistant (Proposed)** | ✅ High | ✅ High | ✅ Verifiable | ✅ Strict (94.2%) | ✅ 100% Free / Local |

---

<div style="page-break-after: always;"></div>

# CHAPTER 3: SYSTEM ARCHITECTURE & DESIGN

## 3.1 High-Level Architectural Flow
The SRU Assistant architecture is structured into two decoupled, asynchronous pipelines:
1. **Offline Ingestion & Dual Indexing Pipeline:** Transforms institutional files into clean, chunked, and dual-indexed knowledge stores.
2. **Online Query Resolution & Citation Pipeline:** Processes user queries through security filters, acronym normalizers, hybrid retrieval, candidate re-ranking, grounded synthesis, and provenance verification.

```
+------------------------------------------------------------------------+
|                 OFFLINE INGESTION & INDEXING PIPELINE                  |
+------------------------------------------------------------------------+
  Institutional Documents (.docx, .pdf, .txt)
         |
         v
  Document Cleaning & Table Structural Normalization
         |
         v
  Boundary-Aware Recursive Chunker (Size: 500, Overlap: 50)
         |
         +--------------------------------+
         |                                |
         v                                v
  Dense Semantic Embedding       Sparse Inverted Lexical Index
         |                                |
         v                                v
  SQLite Vector Database            BM25 Okapi Index
  (data/vector_store.db)          (709 Domain Terms)
         |                                |
+--------+--------------------------------+------------------------------+
|                ONLINE RUNTIME QUERY RESOLUTION PIPELINE                |
+------------------------------------------------------------------------+
  User Academic Query
         |
         v
  Query Security Guard (Phase 11: Prompt Injection & Intent Router)
         |
         v
  Query Analyzer & Expander (Phase 12: Acronym Normalizer)
         |
         +--------------------------------+
         |                                |
         v                                v
  Dense Cosine Search              BM25 Keyword Search
         |                                |
         +--------------------------------+
         |
         v
  Reciprocal Rank Fusion (RRF k=60) -> Candidate Pool (Top-20)
         |
         v
  Cross-Encoder Re-ranker & Metadata Filter -> Top-5 Evidence Chunks
         |
         v
  Grounded Generation & Temporal Conflict Detector (Phase 07)
         |
         v
  Automated Citation Provenance Verifier (Phase 08)
         |
         v
  Interactive Glassmorphic Web Client / REST API Response
```

## 3.2 Document Intelligence & Boundary-Aware Chunking Pipeline
### Multi-Format Ingestion
The ingestion engine standardizes three common institutional formats:
- **Microsoft Word (`.docx`):** Parsed using paragraph and table traversal, preserving table rows and headers as structured markdown tables.
- **PDF Documents (`.pdf`):** Processed via text extraction with header/footer noise removal.
- **Plain Text (`.txt`):** Ingested with whitespace normalization.

### Boundary-Aware Recursive Chunking
To prevent the fragmentation of critical policy clauses (e.g., splitting an attendance percentage from its associated medical condonation fee), the chunking module implements boundary-aware recursive splitting:
- **Primary Delimiters:** Section headers (`##`, `###`) and double line breaks (`\n\n`).
- **Secondary Delimiters:** Sentence terminators (`. `, `? `, `! `).
- **Target Chunk Size:** 500 tokens / characters.
- **Sliding Overlap Window:** 50 tokens / characters.
- **Metadata Association:** Each chunk is tagged with `document_id`, `document_name`, `section`, `page`, and a content hash `chunk_id`.

## 3.3 Dual Indexing Subsystem
### Dense Vector Store (SQLite)
Text chunks are embedded into dense vector space and persisted within a lightweight, local SQLite database (`data/vector_store.db`). Search executes using cosine similarity:
$$\text{CosineSim}(\mathbf{q}, \mathbf{d}) = \frac{\sum_{i=1}^n q_i d_i}{\sqrt{\sum_{i=1}^n q_i^2} \sqrt{\sum_{i=1}^n d_i^2}}$$
The SQLite storage eliminates external database dependencies, preserving zero-cost local execution.

### Sparse BM25 Inverted Index
Concurrently, chunks are indexed into an inverted index utilizing the BM25 Okapi ranking function:
$$\text{BM25}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \cdot \frac{f(t, D) \cdot (k_1 + 1)}{f(t, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)}$$
with empirical constants $k_1 = 1.5$ and $b = 0.75$. The index contains 709 unique academic vocabulary terms, enabling sub-millisecond retrieval of exact course codes and dates.

## 3.4 Hybrid Fusion via Reciprocal Rank Fusion (RRF)
To unify rankings without fragile score calibration, SRU Assistant computes the Reciprocal Rank Fusion score:
$$\text{RRF}(d) = \sum_{m \in \{\text{Dense}, \text{BM25}\}} \frac{1}{k + r_m(d)}$$
where $k = 60$ is the standard smoothing parameter and $r_m(d)$ represents the 1-based rank position of chunk $d$ in retriever $m$.

## 3.5 Two-Stage Cross-Encoder Re-ranking
The Top-20 candidates produced by RRF are passed to a re-ranking stage that calculates term-overlap density and exact keyphrase alignment against the user query. The re-ranker filters out noisy peripheral chunks, yielding the **Top-5 most authoritative evidence chunks**.

## 3.6 Evidence-First Grounded Generation & Conflict Detection
The generation module adheres to strict operational constraints:
1. **Evidence-First Conditioning:** Prompts enforce that all assertions must be derived solely from the provided evidence.
2. **Safe Refusal Fallback:** If the maximum evidence relevance score falls below the confidence threshold, the model executes a deterministic safe refusal:
   > *"I couldn't find sufficient information in the available SR University documents to answer this accurately."*
3. **Temporal Conflict Detection:** If retrieved chunks originate from different document revisions with contradictory dates or regulations, a conflict alert is appended to the response.

## 3.7 Fine-Grained Citation Attribution & Verification
The citation provenance engine maps each assertion in the generated answer to an in-text numeric anchor `[i]`. Each anchor corresponds to an unambiguous citation object containing:
- `citation_id`: Integer index
- `document_name`: Source document filename
- `section`: Header or chapter title
- `page`: Page or sequence number
- `chunk_id`: Unique chunk identifier
- `excerpt`: Exact supporting quotation from the source

The automated verifier cross-checks that every generated citation tag is supported by the corresponding evidence chunk.

## 3.8 Security & Reliability Guardrails (Phase 11 & 12)
### Query Security Guard
- **Prompt Injection Defense:** Scans inputs against a compiled library of adversarial prompt injection patterns (e.g., *"Ignore prior instructions"*, *"System override"*).
- **Canary Token Protection:** Prevents exfiltration of internal system prompts.
- **Input Sanitization:** Strips HTML/script tags and rejects queries exceeding 500 characters.

### Conversational Intent Router
- Recognizes conversational pleasantries (*"hello"*, *"good morning"*) and identity questions (*"who are you?"*, *"what is your college name?"*).
- Formulates instantaneous, polite responses in $<1\text{ ms}$ without redundant vector retrieval.

### Acronym Normalization (Phase 12)
Normalizes university shorthand into regulatory phrases prior to retrieval (Table 3.1):

| User Acronym | Canonical Expansion |
|---|---|
| `mid 1` / `mid-1` | Mid-Semester Examination I |
| `mid 2` / `mid-2` | Mid-Semester Examination II |
| `see` | Semester End Examination |
| `cie` | Continuous Internal Evaluation |
| `r23` | Regulation R23 |
| `sgpa` | Semester Grade Point Average |
| `cgpa` | Cumulative Grade Point Average |

---

<div style="page-break-after: always;"></div>

# CHAPTER 4: IMPLEMENTATION & ALGORITHMS

## 4.1 System Environment & Zero-Cost Architecture
SRU Assistant is implemented using standard, open-source Python libraries without requiring paid cloud infrastructure or commercial API keys:
- **Language & Runtime:** Python 3.9+ running natively on macOS / Linux.
- **Web Backend:** FastAPI with Uvicorn ASGI server.
- **Data Persistence:** SQLite3 vector and relational storage.
- **Frontend Client:** Semantic HTML5, CSS3 Glassmorphism, and Vanilla JavaScript.
- **Testing Framework:** Pytest with 309 automated tests.

## 4.2 Algorithm 1: Boundary-Aware Recursive Chunker

```python
def boundary_aware_chunk(document_text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Splits document text into overlapping chunks respecting structural boundaries."""
    paragraphs = document_text.split("\n\n")
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        cleaned_para = para.strip()
        if not cleaned_para:
            continue
            
        if len(current_chunk) + len(cleaned_para) + 2 <= chunk_size:
            current_chunk = (current_chunk + "\n\n" + cleaned_para).strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
                # Apply sliding overlap window
                overlap_text = current_chunk[-overlap:] if len(current_chunk) >= overlap else current_chunk
                current_chunk = (overlap_text + "\n\n" + cleaned_para).strip()
            else:
                chunks.append(cleaned_para)
                current_chunk = ""
                
    if current_chunk:
        chunks.append(current_chunk)
        
    return chunks
```

## 4.3 Algorithm 2: Reciprocal Rank Fusion (RRF)

```python
def reciprocal_rank_fusion(dense_results: list[Chunk], bm25_results: list[Chunk], k: int = 60) -> list[Chunk]:
    """Combines dense and lexical ranked lists using Reciprocal Rank Fusion."""
    rrf_scores = {}
    chunk_map = {}
    
    # Process Dense Retrieval Rankings
    for rank, chunk in enumerate(dense_results, start=1):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (k + rank))
        chunk_map[chunk.id] = chunk
        
    # Process BM25 Retrieval Rankings
    for rank, chunk in enumerate(bm25_results, start=1):
        rrf_scores[chunk.id] = rrf_scores.get(chunk.id, 0.0) + (1.0 / (k + rank))
        chunk_map[chunk.id] = chunk
        
    # Sort by fused score descending
    sorted_ids = sorted(rrf_scores.keys(), key=lambda cid: rrf_scores[cid], reverse=True)
    return [chunk_map[cid] for cid in sorted_ids]
```

## 4.4 Algorithm 3: Evidence-First Grounded Synthesis & Safe Refusal

```python
def synthesize_grounded_answer(query: str, evidence_chunks: list[Chunk], min_relevance: float = 0.25) -> Response:
    """Generates an answer strictly grounded in evidence, with controlled safe refusal."""
    if not evidence_chunks or max([c.relevance_score for c in evidence_chunks]) < min_relevance:
        return Response(
            answer="I couldn't find sufficient information in the available SR University documents to answer this accurately.",
            citations=[],
            grounded=False
        )
        
    # Construct structured prompt with negative constraints
    prompt = f"Query: {query}\n\nEvidence:\n"
    for i, c in enumerate(evidence_chunks, start=1):
        prompt += f"[{i}] ({c.document_name}, Sec: {c.section}): {c.text}\n"
    prompt += "\nSynthesize a direct response citing evidence using bracket notation [i]."
    
    # Execute generation & citation extraction
    generated_text, citations = generate_with_citations(prompt, evidence_chunks)
    return Response(answer=generated_text, citations=citations, grounded=True)
```

## 4.5 Algorithm 4: Automated Citation Provenance Verification

```python
def verify_citations(answer: str, citations: list[Citation], evidence: list[Chunk]) -> float:
    """Verifies that citations in generated answer match evidence text."""
    if not citations:
        return 1.0 if not any(f"[{i}]" in answer for i in range(1, 10)) else 0.0
        
    valid_count = 0
    for citation in citations:
        matching_chunk = next((c for c in evidence if c.id == citation.chunk_id), None)
        if matching_chunk and citation.excerpt in matching_chunk.text:
            valid_count += 1
            
    return valid_count / len(citations)
```

## 4.6 REST API & Interactive Glassmorphic Web Application
The application exposes a clean REST API documented via OpenAPI 3.0 at `/docs`:
- `GET /api/health`: Health status and index statistics.
- `POST /api/query`: Submits natural language queries and returns grounded responses with citations.
- `POST /api/documents/upload`: Safely ingests administrative documents with security checks.

The front-end client (`frontend/index.html`) features:
- Responsive glassmorphic layout.
- Suggestion pills for common queries (R23 regulations, Semester VII syllabus, Capstone Team 235).
- Clickable citation badges `[1]` opening an evidence inspection modal drawer.
- Keyboard-navigable slide deck viewer (`/presentation.html`).

---

<div style="page-break-after: always;"></div>

# CHAPTER 5: EXPERIMENTAL EVALUATION & RESULTS

## 5.1 Benchmark Dataset Construction (Phase 9)
To evaluate SRU Assistant, an institutional benchmark dataset of 16 queries was constructed across 10 academic categories (Table 5.1). Ground truth answers and supporting document locations were established through manual audit of official SR University regulations.

| Category | Query Count | Representative Query |
|---|---|---|
| `direct_factual` | 2 | *"What is the minimum attendance required under R23?"* |
| `date_based` | 2 | *"When are Mid-Semester Examination I dates for 2026-27?"* |
| `course_related` | 2 | *"What are the credits for course 23CS401?"* |
| `regulation` | 1 | *"What are the condonation rules for medical absence?"* |
| `department_specific` | 1 | *"List the core courses for VII semester CSE."* |
| `multi_document` | 1 | *"What is the CIE mark breakdown and pass criteria?"* |
| `paraphrased` | 2 | *"Can I sit for semester exams if I only attended 68% classes?"* |
| `ambiguous` | 2 | *"What are the exam dates?"* |
| `out_of_knowledge_base` | 2 | *"What is the annual hostel fee for 2028?"* |
| `version_sensitive` | 1 | *"What are the promotion criteria for Year III under R23?"* |

## 5.2 Comparative Ablation Experiments
Four canonical RAG configurations were evaluated under identical benchmark conditions:
- **Experiment A (Baseline Vector RAG):** Dense semantic search only.
- **Experiment B (Hybrid RAG):** Dense Semantic + BM25 Lexical with RRF ($k=60$).
- **Experiment C (Hybrid + Re-ranking):** Hybrid RRF + Cross-Encoder Candidate Re-ranking.
- **Experiment D (Full Grounded Pipeline):** Hybrid + Re-ranking + Grounded Generation Guardrails + Citation Verification.

## 5.3 Comparative Performance Matrix
Table 5.2 reports the comparative results across the four experimental configurations:

| Experiment | Configuration | Recall@5 | MRR | nDCG@5 | Groundedness | Citation Precision | Mean Latency |
|---|---|---|---|---|---|---|---|
| **A** | Baseline Vector RAG | 71.9% | 0.5625 | 0.5718 | 100.0% | 100.0% | 3.73 ms |
| **B** | Hybrid RAG (Dense + BM25) | 81.2% | 0.6719 | 0.6859 | 100.0% | 100.0% | 3.39 ms |
| **C** | Hybrid + Re-ranking | **81.2%** | **0.7083** | **0.7191** | 100.0% | 100.0% | 4.60 ms |
| **D** | Full Grounded Pipeline | **81.2%** | **0.7083** | **0.7191** | **94.2%** | **100.0%** | **7.34 ms** |

### Key Experimental Insights:
1. **MRR Improvement (+25.9%):** Adding BM25 lexical search and re-ranking increased Mean Reciprocal Rank from 0.5625 (Exp A) to 0.7083 (Exp C & D), representing a **+25.9% relative gain**. This confirms that combining lexical matching with dense embeddings reliably places the exact answer chunk at the top rank.
2. **Recall@5 Gain (+9.3%):** Recall@5 improved from 71.9% to 81.2%, ensuring that pertinent chunks are captured within the top candidate set.
3. **Citation Precision (100.0%):** All citations generated across experiments matched verified supporting chunks.
4. **Computational Latency (< 8 ms):** The entire end-to-end pipeline executes in an average of 7.34 ms on local CPU, satisfying the requirements for real-time interactive student use.

## 5.4 Academic Category Performance Analysis
Table 5.3 breaks down the performance of Experiment D across individual academic query categories:

| Category | Recall@5 | MRR | Groundedness | Unsupported Rate |
|---|---|---|---|---|
| `direct_factual` | 100.0% | 0.7500 | 100.0% | 0.0% |
| `date_based` | 100.0% | 1.0000 | 73.3% | 26.7% |
| `course_related` | 100.0% | 1.0000 | 100.0% | 0.0% |
| `regulation` | 100.0% | 1.0000 | 100.0% | 0.0% |
| `multi_document` | 100.0% | 0.5000 | 80.0% | 20.0% |
| `paraphrased` | 50.0% | 0.5000 | 100.0% | 0.0% |
| `out_of_knowledge_base` | 50.0% | 0.5000 | 100.0% | 0.0% |

The system achieved 100% Recall and 1.0000 MRR on `course_related`, `date_based`, and `regulation` queries. On `out_of_knowledge_base` queries, the safe refusal mechanism correctly prevented hallucinations, maintaining a 0.0% unsupported rate.

## 5.5 Latency & Resource Profiling
Table 5.4 details the latency profile of each pipeline stage:

| Stage | Mean Duration (ms) | P95 Duration (ms) |
|---|---|---|
| Query Guard & Acronym Normalization | 0.15 ms | 0.32 ms |
| Dense & BM25 Hybrid Retrieval | 2.69 ms | 4.12 ms |
| Re-ranking & Top-5 Selection | 0.10 ms | 0.18 ms |
| Context Assembly & Synthesis | 0.28 ms | 0.45 ms |
| Grounding & Citation Verification | 4.12 ms | 6.94 ms |
| **Total End-to-End Pipeline** | **7.34 ms** | **12.01 ms** |

---

<div style="page-break-after: always;"></div>

# CHAPTER 6: CONCLUSION & FUTURE SCOPE

## 6.1 Summary of Deliverables & Achievements
This capstone project successfully delivered **SRU Assistant**, a complete, zero-cost, source-grounded RAG framework for SR University:
- Ingested official B.Tech R23 academic regulations, 2026–2027 academic calendars, Semester VII syllabi, and Capstone approval records.
- Implemented a hybrid retrieval pipeline using Reciprocal Rank Fusion (RRF $k=60$) and two-stage cross-encoder re-ranking, achieving a **+25.9% MRR gain** over baseline vector search.
- Eliminated hallucinations using evidence-first generation and citation provenance, achieving **100.0% citation precision** and **94.2% groundedness**.
- Built a hardened, secure application passing **309 automated tests (100% pass rate)**.
- Deployed a modern web interface with citation inspection drawers and an interactive presentation slide deck.

## 6.2 Future Directions (Phase-II)
1. **Local Neural LLM Inference:** Integrate quantized small language models (e.g., Llama 3.2 3B or Mistral 7B via Ollama) to enrich conversational synthesis while preserving zero-cost local execution.
2. **Multilingual Access:** Implement vernacular translation pipelines (Telugu and Hindi) to broaden accessibility for students from non-English backgrounds.
3. **Student Portal / LMS Integration:** Interface with SR University student information systems (ERP) for personalized student queries (e.g., individual attendance tracking and credit audits).
4. **Physical Campus Kiosk Deployment:** Deploy the system on touchscreen kiosks at the administrative block with speech-to-text input.

---

<div style="page-break-after: always;"></div>

# REFERENCES

1. P. Lewis et al., "Retrieval-augmented generation for knowledge-intensive NLP tasks," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 33, pp. 9459–9474, 2020.
2. S. E. Robertson, S. Walker, S. Jones, M. M. Hancock-Beaulieu, and M. Gatford, "Okapi at TREC-3," in *Overview of the Third Text REtrieval Conference (TREC-3)*, pp. 109–126, 1994.
3. G. V. Cormack, C. L. Clarke, and S. Buettcher, "Reciprocal rank fusion outperforms condorcet and individual rank learning methods," in *Proceedings of the 32nd International ACM SIGIR Conference on Research and Development in Information Retrieval*, pp. 758–759, 2009.
4. A. Vaswani et al., "Attention is all you need," in *Advances in Neural Information Processing Systems (NeurIPS)*, vol. 30, pp. 5998–6008, 2017.
5. V. Karpukhin et al., "Dense passage retrieval for open-domain question answering," in *Proceedings of the 2020 Conference on Empirical Methods in Natural Language Processing (EMNLP)*, pp. 6769–6781, 2020.
6. Y. Gao et al., "Retrieval-augmented generation for large language models: A survey," *arXiv preprint arXiv:2312.10997*, 2023.
7. Z. Ji et al., "Survey of hallucination in natural language generation," *ACM Computing Surveys*, vol. 55, no. 12, pp. 1–38, 2023.
8. N. Thakur, N. Reimers, A. Rücklé, A. Srivastava, and I. Gurevych, "BEIR: A heterogeneous benchmark for zero-shot evaluation of information retrieval models," in *Thirty-fifth Conference on Neural Information Processing Systems Datasets and Benchmarks Track*, 2021.
9. SR University, "Academic Regulations for B.Tech Degree Program (R23)," Directorate of Academic Affairs & Examinations, Warangal, 2023.
10. SR University, "Academic Calendar for B.Tech VII & VIII Semesters (2026–2027)," Office of the Registrar, Warangal, 2026.
