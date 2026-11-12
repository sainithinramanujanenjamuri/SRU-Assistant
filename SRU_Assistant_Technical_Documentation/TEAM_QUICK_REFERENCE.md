# SRU Assistant — Team Quick Reference Guide

**System:** SRU Assistant — University Academic Query Resolution RAG Framework  
**Audience:** Capstone Project Team Members, Technical Reviewers & Evaluators  
**Department:** School of Computer Science & AI, SR University  

---

## 1. System in 60 Seconds

SRU Assistant is an enterprise-grade Retrieval-Augmented Generation (RAG) system engineered specifically to resolve student academic inquiries using verified SR University documents (syllabi, academic regulations, examination schedules, and circulars).

Instead of relying on an LLM's unconstrained memory (which invents plausible-sounding dates and regulations), SRU Assistant executes a strict **"Retrieve First, Generate Second, Verify & Cite Every Claim"** paradigm:
1. It validates and analyzes the student's question.
2. It executes a **Dual-Channel Search**: Dense semantic search (SQLite vector database) + Lexical keyword search (BM25 index).
3. It fuses the two ranking lists using **Reciprocal Rank Fusion (RRF)** ($k=60$) and refines candidates with a **Cross-Feature Re-ranker**.
4. It feeds verified chunk excerpts into **Qwen3.5:4b** via a local Ollama daemon.
5. It extracts factual claims from the generated answer and **deterministically verifies citations** against source text.
6. The student receives an answer with clickable citation chips (`[ Academic Regulations · Page 12 ]`) that open the exact official text passage in a drawer.

---

## 2. Key Technologies & Runtime Components

| Layer | Technology | Version / Configuration | Purpose |
| :--- | :--- | :--- | :--- |
| **Backend Framework** | Python 3.11 + FastAPI | `fastapi==0.110+` | REST API layer, async streaming, OpenAPI documentation |
| **Web Server** | Uvicorn (ASGI) | `uvicorn==0.28+` | Serves API and mounted frontend on port 8000 |
| **Database (Vectors)** | SQLite 3 (`sru_vectors.db`) | 384-dimensional binary BLOBs | Embedded vector storage with cosine distance calculation |
| **Lexical Search** | Okapi BM25 (`bm25_index.json`) | $k_1=1.5, b=0.75$, 1387 terms | Keyword search for exact course codes, regulation numbers, and dates |
| **Rank Fusion** | Reciprocal Rank Fusion (RRF) | Constant $k=60$ | Merges dense similarity and BM25 rank scores without calibration drift |
| **Local LLM Engine** | Ollama | `qwen3.5:4b` (`chat` endpoint) | Generates grounded natural-language answers without cloud API costs |
| **Document Loaders** | `pypdf`, `python-docx` | PDF, DOCX, and TXT | Multi-format institutional document text extraction |
| **Chunking Engine** | Structure-Aware Token Chunker | Target: 500, Max: 1200 tokens | Semantic boundary preservation for sections and tables |
| **Frontend UI** | HTML5, CSS3, Vanilla JS (ES6+) | Single-Page Application (SPA) | Student Assistant + System Admin dashboard with zero NPM dependencies |

---

## 3. End-to-End Workflows

### Workflow A: Academic Query Resolution
```
Student Submits Query (UI: "When is Mid-Semester Examination I?")
                      │
                      ▼
POST /api/query (FastAPI Routes)
                      │
                      ▼
QueryGuard: Security Screening & Sanitization (app/security/query_guard.py)
                      │
                      ├─► Threat Detected? ──► Safe Security Refusal
                      ├─► Conversational? ────► Fast Greeting Response
                      ▼
EnhancedRetriever (retrieval/enhanced_retriever.py)
  ├─► AcademicQueryAnalyzer: Extracts entities (Exam terms, dates, regulations)
  ├─► VectorRetriever: Dense similarity search in SQLite vectorstore
  ├─► BM25Retriever: Lexical term frequency match in BM25 index
  ├─► ReciprocalRankFusion: Combines rankings (k=60)
  ├─► MetadataFilter: Applies soft score adjustments (+/- 0.15)
  └─► CrossFeatureReranker: Re-ranks candidates by token density & proximity
                      │
                      ▼
ContextBuilder (generation/prompts/context_builder.py)
  └─► Compiles candidate excerpts within 1500-token budget
                      │
                      ▼
GroundedPromptTemplate + OllamaLLMClient (generation/llm/ollama.py)
  ├─► Injects context and system instructions into Qwen3.5:4b
  └─► Parses raw text, stripping reasoning tags (<think>...</think>)
                      │
                      ▼
Citation Subsystem (citations/)
  ├─► ClaimExtractor: Segments answer into atomic claims
  ├─► CitationMapper: Associates claims with candidate chunks
  ├─► CitationVerifier: Audits exact entity containment & lexical support
  └─► CitationFormatter: Injects bracket tokens ([1], [2]) into response
                      │
                      ▼
QueryResponse returned to Client with Grounding Shield & Clickable Citation Chips!
```

### Workflow B: Official Document Ingestion & Rollback
```
Admin Uploads Document (.pdf, .docx, .txt) via Dropzone
                      │
                      ▼
POST /api/documents/upload?auto_index=true
                      │
                      ▼
DocumentGuard: Bounded 64 KB read up to 25 MB max limit; Magic bytes & SHA-256 hash check
                      │
                      ├─► Duplicate SHA-256? ──► Return duplicate status (no re-indexing)
                      ▼
DocumentPipeline (ingestion/pipeline.py)
  ├─► PDF/DOCX/TXT Loader extracts text and page numbers
  ├─► DocumentCleaner removes repeating headers/footers (> 0.8 page frequency)
  ├─► StructureDetector detects course codes, regulations, semesters, dates
  └─► MetadataExtractor computes category and academic year
                      │
                      ▼
ChunkingPipeline (ingestion/chunking/pipeline.py)
  └─► StructureAwareChunker splits along section headings, tables, and lists
                      │
                      ▼
VectorIndexer (retrieval/vectorstore/indexer.py)
  ├─► FastHash / Embedding model encodes chunk vectors
  └─► Inserts binary BLOB records into SQLite `vector_records`
                      │
                      ▼
BM25Indexer (retrieval/lexical/indexer.py)
  ├─► Tokenizes chunks and updates vocabulary postings
  └─► Atomically flushes updated index to `data/indices/bm25_index.json`
                      │
   [EXCEPTION TRIGGERED AT ANY STAGE?]
   └──► TRANSACTIONAL ROLLBACK:
        1. Purges inserted BM25 chunk entries & re-saves index file
        2. Purges inserted vector records from SQLite
        3. Unlinks chunk dataset JSON file
        4. Unlinks processed intermediate JSON file
        5. Unlinks uploaded raw document file
```

---

## 4. Key Terminology for Technical Evaluations

- **RAG (Retrieval-Augmented Generation)**: Architecture providing authoritative external evidence to an LLM at inference time to prevent hallucination.
- **RRF (Reciprocal Rank Fusion)**: A consensus ranking algorithm that merges ranked lists from disparate retrieval channels using the formula $RRF(d) = \sum \frac{w_m}{k + rank_m(d)}$. It bypasses the problem of incompatible score scales between cosine similarity ($[-1, 1]$) and BM25 ($[0, \infty)$).
- **BM25 (Best Matching 25)**: Probabilistic term-matching algorithm incorporating term frequency saturation and document length normalization. Essential for academic queries containing exact course codes like `23CS201PE408`.
- **Cross-Encoder / Re-ranker**: A secondary ranking model that evaluates the joint token interaction between a user query and candidate passages to re-order the top retrieved candidates before context assembly.
- **Grounding (Faithfulness)**: The mathematical metric evaluating whether statements generated by an LLM are strictly derived from the provided evidence ($1.0 = \text{100\% grounded}$).
- **Citation Precision & Recall**: Precision evaluates whether cited chunks actually support the claim; Recall evaluates whether all factual claims carry appropriate citations.

---

## 5. Defense FAQ for Project Presentation

**Q1: Why did you choose Hybrid RAG over Dense-only vector search?**  
*Answer:* Dense embeddings excel at semantic similarity ("rules for exams") but struggle with precise alphanumeric strings like course codes (`23CS201PE408`), regulation versions (`R23`), or specific room numbers. BM25 guarantees keyword recall for exact terms, while dense search captures semantic intent. Our benchmark demonstrates that hybrid retrieval increased Recall@5 from **71.88%** to **81.25%** and MRR from **0.5625** to **0.6719**.

**Q2: How does SRU Assistant prevent hallucinations?**  
*Answer:* Hallucination prevention operates across three distinct architectural layers:
1. *Pre-generation*: The `ContextBuilder` sets a strict token budget (1500 tokens) and filters low-relevance chunks ($< 0.40$), while the system prompt mandates that the model only answer using supplied evidence.
2. *In-generation*: Low temperature ($0.0$) ensures deterministic sampling without creative improvisation.
3. *Post-generation*: The `CitationVerifier` and `GroundingValidator` segment the answer into atomic claims, check exact entity containment, and calculate support scores.

**Q3: Why SQLite for vector storage instead of Milvus or Pinecone?**  
*Answer:* SQLite is embedded, serverless, zero-maintenance, and requires no external Docker containers or network roundtrips. For an institutional academic assistant managing several hundred official documents (~50,000 chunks), SQLite easily delivers sub-15ms vector retrieval while remaining fully portable and backup-friendly.

**Q4: How does the system handle reasoning models like Qwen3.5?**  
*Answer:* Thinking-capable models like Qwen3.5 generate internal reasoning traces enclosed within `<think>...</think>` tags or inside dedicated payload keys. The `OllamaLLMClient` explicitly captures the thinking trace for telemetry while stripping reasoning tags from the user-facing text, preventing thinking tokens from exhausting the response token budget.
