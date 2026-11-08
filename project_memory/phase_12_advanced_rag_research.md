# Phase 12 — Advanced RAG Research: Query Expansion & Academic Acronym Normalization

## 1. Objective

Enhance the retrieval precision and recall of the SRU Assistant by investigating and implementing domain-tailored query expansion and academic acronym normalization. In an institutional university setting, students frequently submit queries with colloquial or shortened terms such as *"when is mid 1?"*, *"what is my see passing mark?"*, or *"r23 attendance rule"*. A standard vector or lexical search may suffer from vocabulary mismatch or incomplete semantic matching if these acronyms are not expanded to their canonical institutional terms.

---

## 2. Methodology & Implementation

### 2.1 Academic Acronym Dictionary

We implemented an institutional vocabulary mapping in `retrieval/query/analyzer.py` that normalizes shorthand and acronyms into their full regulatory nomenclature:

```python
ACRONYM_EXPANSIONS: dict[str, str] = {
    "mid 1": "Mid-Semester Examination I",
    "mid 2": "Mid-Semester Examination II",
    "mid-1": "Mid-Semester Examination I",
    "mid-2": "Mid-Semester Examination II",
    "mid i": "Mid-Semester Examination I",
    "mid ii": "Mid-Semester Examination II",
    "see": "Semester End Examination",
    "cie": "Continuous Internal Evaluation",
    "r23": "Regulation R23",
    "sgpa": "Semester Grade Point Average",
    "cgpa": "Cumulative Grade Point Average",
    "nlp": "Natural Language Processing",
    "dl": "Deep Learning",
    "cs": "Computer Science",
}
```

### 2.2 Dual Search Formulation

The `QueryAnalyzer` extracts both the raw normalized query and the `expanded_query`. The `EnhancedRetriever` queries the hybrid indexing pipeline (Dense Vector Search + BM25 Lexical Search) using the expanded query formulation:
- **Lexical BM25:** Matches the exact expanded terms (e.g., *"Mid-Semester Examination I"*, *"Semester End Examination"*).
- **Dense Vector Search:** Employs cosine similarity over the expanded query embedding, ensuring high alignment with regulatory chunk embeddings.

---

## 3. Empirical Verification & Evidence

### 3.1 Test Execution

The query analyzer and enhanced retriever were tested with expanded queries:
```bash
.venv/bin/pytest tests/
```

**Output:**
```
============================= 309 passed in 1.05s ==============================
```

### 3.2 Real-World Query Test

| Test Query | Expanded Query | Top Retrieved Chunk |
|---|---|---|
| `"when is mid 1?"` | `"when is Mid-Semester Examination I?"` | `sru_academic_calendar_2026_27.txt` (Schedule: 05 Oct 2026 to 10 Oct 2026) |
| `"what is see weightage?"` | `"what is Semester End Examination weightage?"` | `sru_academic_regulations_r23.txt` (SEE: 60 Marks, 40% passing) |
| `"r23 attendance rule"` | `"Regulation R23 attendance rule"` | `sru_academic_regulations_r23.txt` (Minimum 75%, 65% condonation) |

---

## 4. Milestone Gate Status

- **Code:** `retrieval/query/analyzer.py`, `retrieval/models.py`, `retrieval/enhanced_retriever.py`
- **Tests:** 100% pass rate (309/309)
- **Status:** **COMPLETED**
