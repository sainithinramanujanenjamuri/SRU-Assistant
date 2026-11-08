# SRU Assistant — Phase 9 Quantitative Evaluation Report

- **Report ID:** `eval_report_dd9883ca51bd`
- **Generated At:** `2026-10-06T15:06:41.405581+00:00`
- **Dataset Version:** `1.0.0`
- **Dataset Hash:** `94e21924062ac694...`
- **Total Benchmark Queries:** 16

---

## 1. Executive Summary & Comparative Matrix

Comparative performance across the four canonical RAG configurations:

| Experiment | Configuration | Recall@5 | MRR | Groundedness | Ans. Relevance | Unsupported Rate | Mean Latency |
|---|---|---|---|---|---|---|---|
| **A** | Experiment A: Vector RAG | 71.9% | 0.5625 | 100.0% | 52.5% | 0.0% | 3.73 ms |
| **B** | Experiment B: Hybrid RAG | 81.2% | 0.6719 | 100.0% | 53.2% | 0.0% | 3.39 ms |
| **C** | Experiment C: Hybrid + Re-ranking | 81.2% | 0.7083 | 100.0% | 52.1% | 0.0% | 4.60 ms |
| **D** | Experiment D: Full Grounded Pipeline | 81.2% | 0.7083 | 94.2% | 52.1% | 5.8% | 7.34 ms |

---

## 2. Detailed Retrieval Metrics

| Experiment | Recall@1 | Recall@3 | Recall@5 | Precision@1 | Precision@5 | MRR | nDCG@5 |
|---|---|---|---|---|---|---|---|
| **A** | 0.3438 | 0.7188 | 0.7188 | 0.3750 | 0.1625 | 0.5625 | 0.5718 |
| **B** | 0.4688 | 0.7188 | 0.8125 | 0.5000 | 0.1875 | 0.6719 | 0.6859 |
| **C** | 0.5312 | 0.8125 | 0.8125 | 0.5625 | 0.2375 | 0.7083 | 0.7191 |
| **D** | 0.5312 | 0.8125 | 0.8125 | 0.5625 | 0.2375 | 0.7083 | 0.7191 |

---

## 3. Generation Quality & RAG Triad

| Experiment | Groundedness (Faithfulness) | Answer Relevance | Context Relevance | Factual Correctness (F1) | Completeness |
|---|---|---|---|---|---|
| **A** | 100.0% | 52.5% | 16.2% | 38.9% | 77.5% |
| **B** | 100.0% | 53.2% | 18.8% | 40.6% | 78.1% |
| **C** | 100.0% | 52.1% | 43.8% | 49.8% | 81.2% |
| **D** | 94.2% | 52.1% | 43.8% | 46.3% | 81.2% |

---

## 4. Citation & Source Attribution Metrics

| Experiment | Citation Precision | Citation Recall | Citation Completeness | Evidence Support Score |
|---|---|---|---|---|
| **A** | 100.0% | 100.0% | 100.0% | 1.0000 |
| **B** | 100.0% | 100.0% | 100.0% | 1.0000 |
| **C** | 100.0% | 100.0% | 100.0% | 1.0000 |
| **D** | 100.0% | 94.2% | 94.2% | 0.9333 |

---

## 5. Multi-Stage Latency Profiles (Mean ms)

| Experiment | Retrieval | Context | Conflict | Generation | Grounding | Citation | Total (Mean) | Total (p95) |
|---|---|---|---|---|---|---|---|---|
| **A** | 0.30 | 0.20 | 0.00 | 0.17 | 0.00 | 3.04 | **3.73** | **6.15** |
| **B** | 0.37 | 0.18 | 0.00 | 0.15 | 0.00 | 2.67 | **3.39** | **4.45** |
| **C** | 2.74 | 0.09 | 0.00 | 0.10 | 0.00 | 1.64 | **4.60** | **6.52** |
| **D** | 2.69 | 0.10 | 0.28 | 0.10 | 1.24 | 2.92 | **7.34** | **12.01** |

---

## 6. Academic Category Breakdown (Experiment D)

| Category | Count | Recall@5 | MRR | Groundedness | Ans. Relevance | Unsupported Rate |
|---|---|---|---|---|---|---|
| `direct_factual` | 2 | 100.0% | 0.7500 | 100.0% | 79.5% | 0.0% |
| `date_based` | 2 | 100.0% | 1.0000 | 73.3% | 35.0% | 26.7% |
| `course_related` | 2 | 100.0% | 1.0000 | 100.0% | 58.3% | 0.0% |
| `regulation` | 1 | 100.0% | 1.0000 | 100.0% | 85.7% | 0.0% |
| `department_specific` | 1 | 50.0% | 0.3333 | 100.0% | 57.1% | 0.0% |
| `multi_document` | 1 | 100.0% | 0.5000 | 80.0% | 57.1% | 20.0% |
| `paraphrased` | 2 | 50.0% | 0.5000 | 100.0% | 44.0% | 0.0% |
| `ambiguous` | 2 | 75.0% | 0.7500 | 100.0% | 25.0% | 0.0% |
| `out_of_knowledge_base` | 2 | 50.0% | 0.5000 | 100.0% | 50.0% | 0.0% |
| `version_sensitive` | 1 | 100.0% | 0.5000 | 80.0% | 50.0% | 20.0% |
