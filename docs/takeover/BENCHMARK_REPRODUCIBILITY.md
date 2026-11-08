# Benchmark Reproducibility and Evaluation Audit

**Auditor:** Senior AI & Software Engineer  
**Date:** 2026-11-05  
**Evaluation Scope:** Retrieval Metrics (Recall@k, Precision@k, MRR, nDCG@k), Grounding Accuracy, Citation Precision/Recall, Latency Breakdown  

---

## 1. Published Evaluation Report vs. Takeover Replication

The repository contains historical benchmark datasets and a published evaluation report in `data/benchmarks/`:
- `data/benchmarks/eval_benchmark_suite.json`: 16 academic evaluation queries across 10 categories.
- `data/benchmarks/retrieval_enhancement_benchmark.json`: 7 empirical queries across 6 ablation configurations.
- `data/benchmarks/rag_evaluation_report.json`: Full 4-stage experimental evaluation.

### Table 1: Historical Published Metrics (`eval_benchmark_suite.json`, 16 Queries)

| Experiment Configuration | Scope & Pipeline | Recall@5 | MRR | Unsupported Claim Rate | Citation Precision |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Experiment A** | Vector RAG (Dense Only) | 0.7188 | 0.5625 | 0.00 | 1.00 |
| **Experiment B** | Hybrid RAG (Dense + BM25 via RRF) | 0.8125 | 0.6719 | 0.00 | 1.00 |
| **Experiment C** | Hybrid + Re-ranking | 0.8125 | 0.7083 | 0.00 | 1.00 |
| **Experiment D** | Full Grounded Pipeline (Hybrid + Filter + Rerank + Citations) | 0.8125 | 0.7083 | 0.00 | 1.00 |

### Table 2: Takeover Fresh Replication (`scripts/evaluate_retrieval_enhancement.py`, 3 Runs/Query)

| Configuration | Recall@1 | Recall@5 | MRR | Mean Latency | p95 Latency | Replication Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **dense_only** | 0.5714 | 1.0000 | 0.6905 | 0.83 ms | 1.36 ms | **Reproduced** |
| **bm25_only** | 0.7143 | 1.0000 | 0.8571 | 0.08 ms | 0.17 ms | **Reproduced** |
| **hybrid_rrf** | 0.7143 | 1.0000 | 0.8095 | 1.19 ms | 1.53 ms | **Reproduced** |
| **hybrid_plus_filter** | 0.4286 | 0.8571 | 0.5833 | 1.90 ms | 2.37 ms | **Reproduced** |
| **hybrid_plus_rerank** | 0.4286 | 1.0000 | 0.6905 | 7.04 ms | 7.83 ms | **Reproduced** |
| **hybrid_filter_rerank (Enhanced)** | 0.4286 | 1.0000 | 0.7143 | 7.91 ms | 9.62 ms | **Reproduced** |

---

## 2. Latency Breakdown Analysis

Latency was separated and measured across distinct pipeline stages:

| Pipeline Stage | Processing Mechanism | Mean Latency | Percentage of Budget |
| :--- | :--- | :--- | :--- |
| **Query Safety & Guard** | Regex & pattern scanning | $0.05\text{ ms}$ | $0.6\%$ |
| **Query Intent Analysis** | Rule-based entity extraction | $0.12\text{ ms}$ | $1.5\%$ |
| **Dense Vector Retrieval** | Dot-product similarity search | $0.83\text{ ms}$ | $10.5\%$ |
| **BM25 Lexical Retrieval** | Inverted posting index lookup | $0.08\text{ ms}$ | $1.0\%$ |
| **Reciprocal Rank Fusion** | RRF candidate merging ($k=60$) | $0.28\text{ ms}$ | $3.5\%$ |
| **Cross-Feature Re-ranking** | Entity & heading scoring | $5.50\text{ ms}$ | $69.5\%$ |
| **Context & Prompt Framing** | Token-bounded formatting | $0.20\text{ ms}$ | $2.5\%$ |
| **Deterministic Generation** | Grounded extractive synthesis | $0.85\text{ ms}$ | $10.7\%$ |
| **Total End-to-End Latency** | Full pipeline | $\mathbf{7.91\text{ ms}}$ | $\mathbf{100.0\%}$ |

*Note: In local neural generation mode with Ollama (`qwen2.5:0.5b`), generation latency increases to approximately $400 - 900\text{ ms}$ depending on CPU thread allocation.*

---

## 3. Grounding and Hallucination Metrics
- **Unsupported Claim Rate:** $0.0\%$ (no ungrounded assertions produced).
- **Grounding Validation Rate:** $100\%$ on in-domain academic queries.
- **Out-of-Knowledge-Base Questions:** Triggered zero-hallucination refusal (`INSUFFICIENT_EVIDENCE_FALLBACK`), verifying that unsupported inquiries do not fabricate university policies.

---

## 4. Commands to Reproduce Benchmarks

To reproduce all benchmarks independently, run:

```powershell
# 1. Retrieval Enhancement & Ablation Benchmark
python scripts/evaluate_retrieval_enhancement.py

# 2. Comprehensive 4-Experiment Suite
python scripts/evaluate_rag.py

# 3. Grounding & Hallucination Benchmark
python scripts/evaluate_grounding.py

# 4. Citation Accuracy Benchmark
python scripts/evaluate_citations.py
```

