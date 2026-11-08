from __future__ import annotations


"""CLI script to execute the Phase 7 Grounded Generation benchmark."""

import json
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generation.grounding_benchmark import GroundingBenchmark


def main() -> int:
    print("=" * 80)
    print("SRU ASSISTANT — PHASE 7 GROUNDED GENERATION BENCHMARK")
    print("=" * 80)

    benchmark = GroundingBenchmark(runs_per_query=3)
    print(f"Dataset Version : {benchmark.VERSION}")
    print(f"Dataset Hash    : {benchmark.dataset_hash[:16]}...")
    print(f"Queries Count   : {len(benchmark.queries)}")
    print(f"Generator       : {benchmark.generator.model_name} (Provider: {benchmark.generator.provider_name})")
    print("-" * 80)
    print("Executing multi-run empirical evaluation across canonical grounding categories...")

    results = benchmark.run_benchmark()

    # Save to data/benchmarks/grounding_benchmark.json
    out_dir = Path("data/benchmarks")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "grounding_benchmark.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n[OK] Machine-readable results saved to: {out_file.resolve()}")

    metrics = results["operational_metrics"]
    latency = results["latency_metrics_ms"]

    print("\n" + "=" * 80)
    print("1. OPERATIONAL GROUNDING METRICS")
    print("=" * 80)
    print(f"  Grounding Faithfulness Rate   : {metrics['grounding_faithfulness_rate'] * 100.0:.1f}%")
    print(f"  Hallucination Rate            : {metrics['hallucination_rate'] * 100.0:.1f}%")
    print(f"  No-Answer Accuracy            : {metrics['no_answer_accuracy'] * 100.0:.1f}%")
    print(f"  Exact Entity Preservation Rate: {metrics['exact_entity_preservation_rate'] * 100.0:.1f}%")

    print("\n" + "=" * 80)
    print("2. EMPIRICAL LATENCY METRICS (Deterministic Baseline)")
    print("=" * 80)
    print(f"  Generation Latency (Mean)     : {latency['generation_mean_ms']:.2f} ms")
    print(f"  Generation Latency (Median)   : {latency['generation_median_ms']:.2f} ms")
    print(f"  Total Pipeline Latency (Mean) : {latency['pipeline_mean_ms']:.2f} ms")
    print(f"  Total Pipeline Latency (p95)  : {latency['pipeline_p95_ms']:.2f} ms")

    print("\n" + "=" * 80)
    print("3. CATEGORY QUERY BREAKDOWN")
    print("=" * 80)
    print(f"{'Category':<28} | {'Behavior':<12} | {'Faithful':<8} | {'Preserved':<10} | {'Latency':<10}")
    print("-" * 80)
    for q in results["query_evaluations"]:
        cat = q["category"]
        beh = q["expected_behavior"]
        faith = f"{q['faithfulness_score']:.2f}"
        pres = f"{q['entity_preservation_ratio'] * 100.0:.0f}%"
        lat = f"{q['latency_mean_ms']:.2f} ms"
        print(f"{cat:<28} | {beh:<12} | {faith:<8} | {pres:<10} | {lat:<10}")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
