from __future__ import annotations


"""CLI execution script for Phase 6 Retrieval Enhancement ablation and Top-K benchmark."""

import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from retrieval.reranking_benchmark import RetrievalEnhancementBenchmark


def main() -> int:
    print("=" * 80)
    print("SRU ASSISTANT — PHASE 6 RETRIEVAL ENHANCEMENT BENCHMARK")
    print("=" * 80)

    benchmark = RetrievalEnhancementBenchmark()
    print(f"Dataset Version : {benchmark.DATASET_VERSION}")
    print(f"Dataset Hash    : {benchmark.dataset_hash[:16]}...")
    print(f"Queries Count   : {len(benchmark.dataset)}")
    print(f"Top-K Grid      : {benchmark.top_k_values}")
    print("-" * 80)
    print("Executing multi-run empirical evaluation across 6 ablation configurations...")

    results = benchmark.run_benchmark(num_runs_per_query=3)

    output_path = Path("data/benchmarks/retrieval_enhancement_benchmark.json")
    benchmark.save_results(results, output_path)
    print(f"\n[OK] Machine-readable results saved to: {output_path.resolve()}\n")

    # 1. Ablation Comparison Summary Table (at K=5)
    print("=" * 80)
    print("1. ABLATION STUDY COMPARISON (Top-K = 5)")
    print("=" * 80)
    print(f"{'Configuration':<30} | {'Recall@1':<8} | {'Recall@5':<8} | {'MRR':<6} | {'Latency (mean)':<14} | {'p95 Latency':<12}")
    print("-" * 80)

    for config_name, k_data in results["ablations"].items():
        m = k_data.get("k_5", {})
        r1 = m.get("recall_at_1", 0.0)
        r5 = m.get("recall_at_5", 0.0)
        mrr = m.get("mrr", 0.0)
        lat = m.get("latency_ms", {})
        mean_lat = f"{lat.get('mean', 0.0):.2f} ms"
        p95_lat = f"{lat.get('p95', 0.0):.2f} ms"
        print(f"{config_name:<30} | {r1:<8.4f} | {r5:<8.4f} | {mrr:<6.4f} | {mean_lat:<14} | {p95_lat:<12}")

    # 2. Top-K Tuning Grid for Full Enhanced Pipeline (hybrid_filter_rerank)
    print("\n" + "=" * 80)
    print("2. TOP-K TUNING EXPERIMENT (Hybrid + Metadata Filtering + Re-ranking)")
    print("=" * 80)
    print(f"{'K':<6} | {'Recall@1':<8} | {'Recall@3':<8} | {'Recall@5':<8} | {'MRR':<6} | {'Mean Latency':<14} | {'p95 Latency':<12}")
    print("-" * 80)

    enhanced_data = results["ablations"].get("hybrid_filter_rerank", {})
    for k in benchmark.top_k_values:
        m = enhanced_data.get(f"k_{k}", {})
        r1 = m.get("recall_at_1", 0.0)
        r3 = m.get("recall_at_3", 0.0)
        r5 = m.get("recall_at_5", 0.0)
        mrr = m.get("mrr", 0.0)
        lat = m.get("latency_ms", {})
        mean_lat = f"{lat.get('mean', 0.0):.2f} ms"
        p95_lat = f"{lat.get('p95', 0.0):.2f} ms"
        print(f"{k:<6} | {r1:<8.4f} | {r3:<8.4f} | {r5:<8.4f} | {mrr:<6.4f} | {mean_lat:<14} | {p95_lat:<12}")

    # 3. Category Breakdown (Recall@5 across 7 academic categories)
    print("\n" + "=" * 80)
    print("3. ACADEMIC CATEGORY BREAKDOWN (Recall@5)")
    print("=" * 80)
    print(f"{'Category':<24} | {'Dense':<7} | {'BM25':<7} | {'Hybrid':<7} | {'Enhanced (F)':<12}")
    print("-" * 80)
    for cat, conf_scores in results["category_breakdown"].items():
        d_hit = conf_scores.get("dense_only", 0.0)
        b_hit = conf_scores.get("bm25_only", 0.0)
        h_hit = conf_scores.get("hybrid_rrf", 0.0)
        f_hit = conf_scores.get("hybrid_filter_rerank", 0.0)
        print(f"{cat:<24} | {d_hit:<7.2f} | {b_hit:<7.2f} | {h_hit:<7.2f} | {f_hit:<12.2f}")

    print("=" * 80)
    return 0


if __name__ == "__main__":
    sys.exit(main())
