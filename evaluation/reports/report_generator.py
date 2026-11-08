"""Report generation utilities for SRU Assistant evaluation benchmarks.

Produces machine-readable JSON exports and formatted Markdown comparative reports.
"""
from __future__ import annotations



import json
from pathlib import Path

from evaluation.models import CANONICAL_BENCHMARK_CATEGORIES, EvaluationReport


class ReportGenerator:
    """Generates structured JSON and Markdown comparative reports from an EvaluationReport."""

    def save_json(self, report: EvaluationReport, output_path: Path | str) -> None:
        """Serialize EvaluationReport to a JSON file."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(report.model_dump(), f, indent=2)

    def generate_markdown(self, report: EvaluationReport) -> str:
        """Format an EvaluationReport into a comprehensive Markdown document."""
        lines: list[str] = [
            "# SRU Assistant — Phase 9 Quantitative Evaluation Report",
            "",
            f"- **Report ID:** `{report.report_id}`",
            f"- **Generated At:** `{report.generated_at}`",
            f"- **Dataset Version:** `{report.dataset_version}`",
            f"- **Dataset Hash:** `{report.dataset_hash[:16]}...`",
            f"- **Total Benchmark Queries:** {report.total_queries}",
            "",
            "---",
            "",
            "## 1. Executive Summary & Comparative Matrix",
            "",
            "Comparative performance across the four canonical RAG configurations:",
            "",
            "| Experiment | Configuration | Recall@5 | MRR | Groundedness | Ans. Relevance | Unsupported Rate | Mean Latency |",
            "|---|---|---|---|---|---|---|---|",
        ]

        for exp_id, exp in report.experiments.items():
            r5 = exp.aggregate_retrieval.recall_at_k.get(5, 0.0)
            mrr = exp.aggregate_retrieval.mrr
            grd = exp.aggregate_generation.groundedness
            ans = exp.aggregate_generation.answer_relevance
            uns = exp.aggregate_generation.unsupported_claim_rate
            lat = exp.aggregate_latency_ms.get("total", {}).get("mean", 0.0)
            lines.append(
                f"| **{exp_id}** | {exp.name} | {r5 * 100:.1f}% | {mrr:.4f} | {grd * 100:.1f}% | {ans * 100:.1f}% | {uns * 100:.1f}% | {lat:.2f} ms |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 2. Detailed Retrieval Metrics",
            "",
            "| Experiment | Recall@1 | Recall@3 | Recall@5 | Precision@1 | Precision@5 | MRR | nDCG@5 |",
            "|---|---|---|---|---|---|---|---|",
        ])

        for exp_id, exp in report.experiments.items():
            r1 = exp.aggregate_retrieval.recall_at_k.get(1, 0.0)
            r3 = exp.aggregate_retrieval.recall_at_k.get(3, 0.0)
            r5 = exp.aggregate_retrieval.recall_at_k.get(5, 0.0)
            p1 = exp.aggregate_retrieval.precision_at_k.get(1, 0.0)
            p5 = exp.aggregate_retrieval.precision_at_k.get(5, 0.0)
            mrr = exp.aggregate_retrieval.mrr
            ndcg = exp.aggregate_retrieval.ndcg_at_k.get(5, 0.0)
            lines.append(
                f"| **{exp_id}** | {r1:.4f} | {r3:.4f} | {r5:.4f} | {p1:.4f} | {p5:.4f} | {mrr:.4f} | {ndcg:.4f} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 3. Generation Quality & RAG Triad",
            "",
            "| Experiment | Groundedness (Faithfulness) | Answer Relevance | Context Relevance | Factual Correctness (F1) | Completeness |",
            "|---|---|---|---|---|---|",
        ])

        for exp_id, exp in report.experiments.items():
            grd = exp.aggregate_generation.groundedness
            ans = exp.aggregate_generation.answer_relevance
            ctx = exp.aggregate_generation.context_relevance
            cor = exp.aggregate_generation.correctness
            com = exp.aggregate_generation.completeness
            lines.append(
                f"| **{exp_id}** | {grd * 100:.1f}% | {ans * 100:.1f}% | {ctx * 100:.1f}% | {cor * 100:.1f}% | {com * 100:.1f}% |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 4. Citation & Source Attribution Metrics",
            "",
            "| Experiment | Citation Precision | Citation Recall | Citation Completeness | Evidence Support Score |",
            "|---|---|---|---|---|",
        ])

        for exp_id, exp in report.experiments.items():
            cp = exp.aggregate_citation.citation_precision
            cr = exp.aggregate_citation.citation_recall
            cc = exp.aggregate_citation.citation_completeness
            es = exp.aggregate_citation.evidence_support
            lines.append(
                f"| **{exp_id}** | {cp * 100:.1f}% | {cr * 100:.1f}% | {cc * 100:.1f}% | {es:.4f} |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 5. Multi-Stage Latency Profiles (Mean ms)",
            "",
            "| Experiment | Retrieval | Context | Conflict | Generation | Grounding | Citation | Total (Mean) | Total (p95) |",
            "|---|---|---|---|---|---|---|---|---|",
        ])

        for exp_id, exp in report.experiments.items():
            lats = exp.aggregate_latency_ms
            ret_m = lats.get("retrieval", {}).get("mean", 0.0)
            ctx_m = lats.get("context", {}).get("mean", 0.0)
            cnf_m = lats.get("conflict", {}).get("mean", 0.0)
            gen_m = lats.get("generation", {}).get("mean", 0.0)
            grd_m = lats.get("grounding", {}).get("mean", 0.0)
            cit_m = lats.get("citation", {}).get("mean", 0.0)
            tot_m = lats.get("total", {}).get("mean", 0.0)
            tot_p95 = lats.get("total", {}).get("p95", 0.0)
            lines.append(
                f"| **{exp_id}** | {ret_m:.2f} | {ctx_m:.2f} | {cnf_m:.2f} | {gen_m:.2f} | {grd_m:.2f} | {cit_m:.2f} | **{tot_m:.2f}** | **{tot_p95:.2f}** |"
            )

        lines.extend([
            "",
            "---",
            "",
            "## 6. Academic Category Breakdown (Experiment D)",
            "",
            "| Category | Count | Recall@5 | MRR | Groundedness | Ans. Relevance | Unsupported Rate |",
            "|---|---|---|---|---|---|---|",
        ])

        exp_d = report.experiments.get("D")
        if exp_d and exp_d.category_metrics:
            for cat in CANONICAL_BENCHMARK_CATEGORIES:
                cm = exp_d.category_metrics.get(cat, {})
                c_cnt = cm.get("count", 0)
                c_r5 = cm.get("recall_at_5", 0.0)
                c_mrr = cm.get("mrr", 0.0)
                c_grd = cm.get("groundedness", 0.0)
                c_ans = cm.get("answer_relevance", 0.0)
                c_uns = cm.get("unsupported_claim_rate", 0.0)
                lines.append(
                    f"| `{cat}` | {c_cnt} | {c_r5 * 100:.1f}% | {c_mrr:.4f} | {c_grd * 100:.1f}% | {c_ans * 100:.1f}% | {c_uns * 100:.1f}% |"
                )

        lines.append("")
        return "\n".join(lines)

    def save_markdown(self, report: EvaluationReport, output_path: Path | str) -> None:
        """Write formatted Markdown report to file."""
        target = Path(output_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        content = self.generate_markdown(report)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
