from __future__ import annotations


"""CLI execution script for Phase 9 RAG Evaluation Benchmark across Experiments A, B, C, D."""

import argparse
import sys
from pathlib import Path

# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import get_settings
from evaluation.datasets.benchmark_loader import BenchmarkDatasetLoader
from evaluation.evaluator import RAGEvaluator
from evaluation.models import CANONICAL_BENCHMARK_CATEGORIES
from evaluation.reports.report_generator import ReportGenerator


def parse_args() -> argparse.Namespace:
    settings = get_settings()
    parser = argparse.ArgumentParser(
        description="SRU Assistant — Phase 9 Quantitative RAG Evaluation Benchmark",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--experiments",
        "-e",
        nargs="+",
        default=["all"],
        help="Experiments to run: 'all', or subset from ['A', 'B', 'C', 'D']",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="data/benchmarks/eval_benchmark_suite.json",
        help="Path to evaluation benchmark dataset JSON",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default="data/benchmarks/rag_evaluation_report.json",
        help="Path to save machine-readable JSON evaluation report",
    )
    parser.add_argument(
        "--markdown",
        "-m",
        type=str,
        default="evaluation/reports/evaluation_report.md",
        help="Path to save Markdown evaluation report",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        choices=list(CANONICAL_BENCHMARK_CATEGORIES),
        help="Optional: filter evaluation to a specific canonical academic category",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=settings.llm_provider,
        help="Generator provider: deterministic, ollama",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=settings.llm_model,
        help="Generator model identifier",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=settings.retrieval_top_k,
        help="Number of retrieved chunks per query",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=settings.vectorstore_path,
        help="Path to SQLite vector store database",
    )
    parser.add_argument(
        "--bm25-path",
        type=str,
        default=str(settings.bm25_index_path),
        help="Path to BM25 index JSON",
    )
    return parser.parse_args()


def print_table_header(title: str) -> None:
    print("\n" + "=" * 92)
    print(f"{title}")
    print("=" * 92)


def main() -> int:
    args = parse_args()

    print("=" * 92)
    print("SRU ASSISTANT — PHASE 9 QUANTITATIVE RAG EVALUATION BENCHMARK")
    print("=" * 92)

    # 1. Load dataset
    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"Error: Benchmark dataset not found at '{dataset_path.resolve()}'.")
        return 1

    loader = BenchmarkDatasetLoader(dataset_path=dataset_path)
    queries = loader.queries

    if args.category:
        queries = loader.get_by_category(args.category)
        print(f"Filtering evaluation to Category: '{args.category}' ({len(queries)} queries)")

    print(f"Dataset Version : {loader.dataset_version}")
    print(f"Dataset Hash    : {loader.dataset_hash[:16]}...")
    print(f"Total Queries   : {len(queries)}")
    print(f"Generator       : {args.provider} ({args.model})")
    print(f"Top-K           : {args.top_k}")

    # Determine experiments
    if "all" in args.experiments:
        exp_keys = ["A", "B", "C", "D"]
    else:
        exp_keys = [k.upper() for k in args.experiments]

    print(f"Experiments     : {', '.join(exp_keys)}")
    print("-" * 92)
    print("Executing automated benchmark runs across RAG configurations...")

    # 2. Instantiate Evaluator
    evaluator = RAGEvaluator(
        loader=loader,
        db_path=args.db_path,
        bm25_path=args.bm25_path,
    )

    # 3. Run Experiments
    report = evaluator.run_all_experiments(
        experiment_keys=exp_keys,
        queries=queries,
        top_k=args.top_k,
        generator_provider=args.provider,
        generator_model=args.model,
    )

    # 4. Save artifacts
    reporter = ReportGenerator()
    if args.output:
        reporter.save_json(report, args.output)
        print(f"\n[OK] Machine-readable report saved to: {Path(args.output).resolve()}")

    if args.markdown:
        reporter.save_markdown(report, args.markdown)
        print(f"[OK] Formatted Markdown report saved to: {Path(args.markdown).resolve()}")

    # 5. Pretty-print Terminal Tables

    # Table 1: Executive Comparative Summary
    print_table_header("1. EXECUTIVE COMPARATIVE SUMMARY MATRIX")
    print(
        f"{'Exp':<4} | {'Configuration':<30} | {'Recall@5':<9} | {'MRR':<6} | {'Grounded':<9} | {'Ans. Rel':<9} | {'Unsupp.':<8} | {'Latency':<10}"
    )
    print("-" * 92)
    for exp_id, exp in report.experiments.items():
        r5 = exp.aggregate_retrieval.recall_at_k.get(5, 0.0) * 100
        mrr = exp.aggregate_retrieval.mrr
        grd = exp.aggregate_generation.groundedness * 100
        ans = exp.aggregate_generation.answer_relevance * 100
        uns = exp.aggregate_generation.unsupported_claim_rate * 100
        lat = exp.aggregate_latency_ms.get("total", {}).get("mean", 0.0)
        print(
            f"{exp_id:<4} | {exp.name:<30} | {r5:>7.1f}% | {mrr:>6.4f} | {grd:>7.1f}% | {ans:>7.1f}% | {uns:>6.1f}% | {lat:>7.2f} ms"
        )

    # Table 2: Detailed Retrieval Metrics
    print_table_header("2. INFORMATION RETRIEVAL METRICS")
    print(
        f"{'Exp':<4} | {'Recall@1':<9} | {'Recall@3':<9} | {'Recall@5':<9} | {'Prec@1':<8} | {'Prec@5':<8} | {'MRR':<6} | {'nDCG@5':<8}"
    )
    print("-" * 92)
    for exp_id, exp in report.experiments.items():
        r1 = exp.aggregate_retrieval.recall_at_k.get(1, 0.0)
        r3 = exp.aggregate_retrieval.recall_at_k.get(3, 0.0)
        r5 = exp.aggregate_retrieval.recall_at_k.get(5, 0.0)
        p1 = exp.aggregate_retrieval.precision_at_k.get(1, 0.0)
        p5 = exp.aggregate_retrieval.precision_at_k.get(5, 0.0)
        mrr = exp.aggregate_retrieval.mrr
        ndcg = exp.aggregate_retrieval.ndcg_at_k.get(5, 0.0)
        print(
            f"{exp_id:<4} | {r1:>9.4f} | {r3:>9.4f} | {r5:>9.4f} | {p1:>8.4f} | {p5:>8.4f} | {mrr:>6.4f} | {ndcg:>8.4f}"
        )

    # Table 3: Generation Quality & RAG Triad
    print_table_header("3. GENERATION QUALITY & RAG TRIAD")
    print(
        f"{'Exp':<4} | {'Groundedness (Faithful)':<24} | {'Ans. Relevance':<15} | {'Ctx. Relevance':<15} | {'Correctness':<12} | {'Completeness':<12}"
    )
    print("-" * 92)
    for exp_id, exp in report.experiments.items():
        grd = exp.aggregate_generation.groundedness * 100
        ans = exp.aggregate_generation.answer_relevance * 100
        ctx = exp.aggregate_generation.context_relevance * 100
        cor = exp.aggregate_generation.correctness * 100
        com = exp.aggregate_generation.completeness * 100
        print(
            f"{exp_id:<4} | {grd:>22.1f}% | {ans:>13.1f}% | {ctx:>13.1f}% | {cor:>10.1f}% | {com:>10.1f}%"
        )

    # Table 4: Citation Metrics
    print_table_header("4. CITATION ATTRIBUTION & PROVENANCE METRICS")
    print(
        f"{'Exp':<4} | {'Citation Precision':<20} | {'Citation Recall':<18} | {'Completeness':<15} | {'Evidence Support':<18}"
    )
    print("-" * 92)
    for exp_id, exp in report.experiments.items():
        cp = exp.aggregate_citation.citation_precision * 100
        cr = exp.aggregate_citation.citation_recall * 100
        cc = exp.aggregate_citation.citation_completeness * 100
        es = exp.aggregate_citation.evidence_support
        print(
            f"{exp_id:<4} | {cp:>18.1f}% | {cr:>16.1f}% | {cc:>13.1f}% | {es:>16.4f}"
        )

    # Table 5: Latency Breakdown (Mean ms)
    print_table_header("5. PIPELINE STAGE LATENCY PROFILES (Mean ms)")
    print(
        f"{'Exp':<4} | {'Retrieval':<10} | {'Context':<9} | {'Conflict':<9} | {'Generation':<11} | {'Grounding':<10} | {'Citation':<9} | {'Total':<10}"
    )
    print("-" * 92)
    for exp_id, exp in report.experiments.items():
        lats = exp.aggregate_latency_ms
        ret_m = lats.get("retrieval", {}).get("mean", 0.0)
        ctx_m = lats.get("context", {}).get("mean", 0.0)
        cnf_m = lats.get("conflict", {}).get("mean", 0.0)
        gen_m = lats.get("generation", {}).get("mean", 0.0)
        grd_m = lats.get("grounding", {}).get("mean", 0.0)
        cit_m = lats.get("citation", {}).get("mean", 0.0)
        tot_m = lats.get("total", {}).get("mean", 0.0)
        print(
            f"{exp_id:<4} | {ret_m:>8.2f} ms | {ctx_m:>7.2f} ms | {cnf_m:>7.2f} ms | {gen_m:>9.2f} ms | {grd_m:>8.2f} ms | {cit_m:>7.2f} ms | {tot_m:>8.2f} ms"
        )

    # Table 6: Category Breakdown for Experiment D
    exp_d = report.experiments.get("D")
    if exp_d and exp_d.category_metrics:
        print_table_header("6. CANONICAL ACADEMIC CATEGORY BREAKDOWN (Experiment D: Full Grounded)")
        print(
            f"{'Category':<24} | {'Count':<5} | {'Recall@5':<9} | {'MRR':<6} | {'Grounded':<9} | {'Ans. Rel':<9} | {'Unsupp.':<8}"
        )
        print("-" * 92)
        for cat in CANONICAL_BENCHMARK_CATEGORIES:
            cm = exp_d.category_metrics.get(cat, {})
            c_cnt = cm.get("count", 0)
            c_r5 = cm.get("recall_at_5", 0.0) * 100
            c_mrr = cm.get("mrr", 0.0)
            c_grd = cm.get("groundedness", 0.0) * 100
            c_ans = cm.get("answer_relevance", 0.0) * 100
            c_uns = cm.get("unsupported_claim_rate", 0.0) * 100
            print(
                f"{cat:<24} | {c_cnt:<5} | {c_r5:>7.1f}% | {c_mrr:>6.4f} | {c_grd:>7.1f}% | {c_ans:>7.1f}% | {c_uns:>6.1f}%"
            )

    print("=" * 92)
    return 0


if __name__ == "__main__":
    sys.exit(main())
