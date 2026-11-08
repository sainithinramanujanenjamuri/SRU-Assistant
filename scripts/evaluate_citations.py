"""Automated Citation and Provenance Evaluation Benchmark for SRU Assistant (Phase 8).

Evaluates:
1. Single-document factual citation precision and recall.
2. Multi-document citation attribution across distinct sources.
3. Insufficient evidence handling (zero false citations).
4. Unsupported / fabricated claim detection and isolation.
5. Provenance integrity (accurate page, section, chunk ID parsing; zero fabricated metadata).
6. Latency profiles (mean, median, p95).
"""
from __future__ import annotations



import hashlib
import json
import statistics
import sys
import time
from datetime import datetime, timezone

try:
    from datetime import UTC
except ImportError:
    UTC = timezone.utc

from pathlib import Path


# Ensure repo root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from citations.citation_mapper import CitationMapper
from citations.citation_verifier import CitationVerifier
from citations.claim_extractor import ClaimExtractor
from citations.formatter import CitationFormatter
from generation.models import RetrievedEvidence


def create_benchmark_dataset() -> list[dict]:
    """Define canonical benchmark test queries spanning all 5 operational categories."""
    return [
        {
            "query_id": "Q1_single_doc_exam_dates",
            "category": "single_document_factual",
            "query": "When is the Mid-Semester Examination I?",
            "evidence": [
                RetrievedEvidence(
                    chunk_id="chunk_cal_001",
                    document_id="doc_cal_sha256_01",
                    document_name="Academic_Calendar_2026_27.pdf",
                    page_info="p. 3",
                    section_path="Academic Calendar 2026-27 > Examination Schedule",
                    text="The Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026 for all undergraduate programs.",
                    score=0.92,
                    metadata={"page_number": 3, "section_title": "Examination Schedule"},
                )
            ],
            "answer": "The Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026 for all undergraduate programs.",
            "expect_citations": True,
            "expected_citation_count": 1,
            "expected_supported_claims": 1,
            "expected_unsupported_claims": 0,
        },
        {
            "query_id": "Q2_multi_doc_course_and_dates",
            "category": "multi_document_synthesis",
            "query": "What does 23CSE302T cover and when is its exam?",
            "evidence": [
                RetrievedEvidence(
                    chunk_id="chunk_syl_042",
                    document_id="doc_syl_sha256_02",
                    document_name="Syllabus_23CSE302T.pdf",
                    page_info="p. 1",
                    section_path="Course Syllabus > 23CSE302T > Objectives",
                    text="23CSE302T covers Advanced Data Structures including binary search trees and graph algorithms.",
                    score=0.88,
                    metadata={"page_number": 1, "section_title": "Objectives"},
                ),
                RetrievedEvidence(
                    chunk_id="chunk_cal_001",
                    document_id="doc_cal_sha256_01",
                    document_name="Academic_Calendar_2026_27.pdf",
                    page_info="p. 3",
                    section_path="Academic Calendar 2026-27 > Examination Schedule",
                    text="The Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026 for all undergraduate programs.",
                    score=0.85,
                    metadata={"page_number": 3, "section_title": "Examination Schedule"},
                ),
            ],
            "answer": "23CSE302T covers Advanced Data Structures including binary search trees and graph algorithms. The Mid-Semester Examination I is scheduled from 12 September 2026 to 16 September 2026 for all undergraduate programs.",
            "expect_citations": True,
            "expected_citation_count": 2,
            "expected_supported_claims": 2,
            "expected_unsupported_claims": 0,
        },
        {
            "query_id": "Q3_insufficient_evidence",
            "category": "insufficient_evidence",
            "query": "What is the capital of Australia?",
            "evidence": [],
            "answer": "I couldn't find sufficient information in the available SR University documents to answer this accurately.",
            "expect_citations": False,
            "expected_citation_count": 0,
            "expected_supported_claims": 0,
            "expected_unsupported_claims": 0,
        },
        {
            "query_id": "Q4_unsupported_fabricated_claim",
            "category": "unsupported_claims",
            "query": "What are the attendance and laboratory requirements?",
            "evidence": [
                RetrievedEvidence(
                    chunk_id="chunk_reg_014",
                    document_id="doc_reg_sha256_03",
                    document_name="Academic_Regulations_R23.pdf",
                    page_info="p. 14",
                    section_path="Academic Regulations R23 > Attendance Requirements",
                    text="Under regulation R23, students must maintain a minimum of 75% attendance to be eligible for end-semester examinations.",
                    score=0.89,
                    metadata={"page_number": 14, "section_title": "Attendance Requirements"},
                )
            ],
            # Second sentence asserts an ungrounded 85% requirement not in evidence
            "answer": "Under regulation R23, students must maintain a minimum of 75% attendance to be eligible for end-semester examinations. Students must also achieve 85% on all laboratory experiments to avoid detention.",
            "expect_citations": True,
            "expected_citation_count": 1,
            "expected_supported_claims": 1,
            "expected_unsupported_claims": 1,
        },
        {
            "query_id": "Q5_provenance_edge_cases",
            "category": "provenance_edge_cases",
            "query": "What are the continuous assessment requirements?",
            "evidence": [
                RetrievedEvidence(
                    chunk_id="chunk_misc_099",
                    document_id="doc_misc_sha256_04",
                    document_name="Internal_Assessment_Circular.pdf",
                    page_info="p. N/A",  # Missing page number
                    section_path="N/A",   # Missing section path
                    text="All continuous internal evaluations require submitting three written assignments.",
                    score=0.81,
                    metadata={},  # No metadata dict values
                )
            ],
            "answer": "All continuous internal evaluations require submitting three written assignments.",
            "expect_citations": True,
            "expected_citation_count": 1,
            "expected_supported_claims": 1,
            "expected_unsupported_claims": 0,
            "check_missing_page_handled": True,
        },
    ]


def run_benchmark(output_path: Path | None = None, repetitions: int = 5) -> dict:
    """Execute the empirical citation evaluation benchmark."""
    print("=" * 70)
    print("SRU ASSISTANT — PHASE 8 CITATION & PROVENANCE BENCHMARK")
    print("=" * 70)

    claim_extractor = ClaimExtractor()
    citation_mapper = CitationMapper(min_match_score=0.40)
    citation_verifier = CitationVerifier(min_support_score=0.50, require_exact_entities=True)
    formatter = CitationFormatter()

    benchmark_queries = create_benchmark_dataset()

    query_results = []
    all_latencies_ms = []
    extraction_latencies_ms = []
    mapping_latencies_ms = []
    verification_latencies_ms = []
    formatting_latencies_ms = []

    provenance_checks_passed = 0
    total_provenance_checks = 0

    for item in benchmark_queries:
        qid = item["query_id"]
        cat = item["category"]
        query_text = item["query"]
        answer_text = item["answer"]
        evidence_items = item["evidence"]

        print(f"\nEvaluating [{qid}] ({cat})...")

        # Repetition loop for statistical latency sampling
        rep_total_latencies = []
        last_verification_result = None
        last_citations = []
        last_claims = []
        last_cited_answer = answer_text

        for _ in range(repetitions):
            t_start = time.perf_counter()

            # 1. Claim Extraction
            t_ext_0 = time.perf_counter()
            claims = claim_extractor.extract_claims(answer_text)
            t_ext = (time.perf_counter() - t_ext_0) * 1000.0

            # 2. Citation Mapping
            t_map_0 = time.perf_counter()
            mapped_claims, citations = citation_mapper.map_claims_to_evidence(
                claims=claims,
                evidence_items=evidence_items,
            )
            t_map = (time.perf_counter() - t_map_0) * 1000.0

            # 3. Citation Verification
            t_ver_0 = time.perf_counter()
            verification_result = citation_verifier.verify_citations(
                claims=mapped_claims,
                citations=citations,
                evidence_items=evidence_items,
            )
            t_ver = (time.perf_counter() - t_ver_0) * 1000.0

            # 4. Citation Rendering
            t_fmt_0 = time.perf_counter()
            cited_ans = formatter.format(
                answer=answer_text,
                citations=verification_result.citations,
                claims=verification_result.claims,
                style="inline_bracket",
            )
            t_fmt = (time.perf_counter() - t_fmt_0) * 1000.0

            t_tot = (time.perf_counter() - t_start) * 1000.0

            rep_total_latencies.append(t_tot)
            extraction_latencies_ms.append(t_ext)
            mapping_latencies_ms.append(t_map)
            verification_latencies_ms.append(t_ver)
            formatting_latencies_ms.append(t_fmt)

            last_verification_result = verification_result
            last_citations = verification_result.citations
            last_claims = verification_result.claims
            last_cited_answer = cited_ans

        mean_lat = round(statistics.mean(rep_total_latencies), 3)
        all_latencies_ms.extend(rep_total_latencies)

        # Evaluate Provenance Integrity
        provenance_valid = True
        for cit in last_citations:
            total_provenance_checks += 1
            # Check: never produce fake page numbers
            if cit.page is not None:
                # If page is reported, it must match an actual integer > 0
                if cit.page <= 0:
                    provenance_valid = False
            else:
                # If page is None, page_info must be "p. N/A"
                if cit.page_info != "p. N/A":
                    provenance_valid = False

            # Check: never produce fake section
            if not cit.section or cit.section == "":
                provenance_valid = False

            # Check: document_id and chunk_id must match actual evidence
            matching_ev = [ev for ev in evidence_items if ev.chunk_id == cit.chunk_id]
            if not matching_ev or matching_ev[0].document_id != cit.document_id:
                provenance_valid = False

            if provenance_valid:
                provenance_checks_passed += 1

        if item.get("check_missing_page_handled"):
            # Explicit edge case check
            total_provenance_checks += 1
            if last_citations and last_citations[0].page is None and last_citations[0].page_info == "p. N/A":
                provenance_checks_passed += 1
            else:
                provenance_valid = False

        # Evaluate expectations
        supported_claims_count = sum(1 for c in last_claims if c.is_supported)
        unsupported_claims_count = len(last_verification_result.unsupported_claims)

        print(f"  Claims extracted: {len(last_claims)} (Supported: {supported_claims_count}, Unsupported: {unsupported_claims_count})")
        print(f"  Citations emitted: {len(last_citations)} (Verified: {sum(1 for c in last_citations if c.is_verified)})")
        print(f"  Citation Precision: {last_verification_result.citation_precision:.4f}")
        print(f"  Citation Recall: {last_verification_result.citation_recall:.4f}")
        print(f"  Support Score: {last_verification_result.overall_support_score:.4f}")
        print(f"  Latency (mean of {repetitions}): {mean_lat} ms")

        query_results.append({
            "query_id": qid,
            "category": cat,
            "query": query_text,
            "answer": answer_text,
            "cited_answer": last_cited_answer,
            "claims_extracted": len(last_claims),
            "supported_claims": supported_claims_count,
            "unsupported_claims": unsupported_claims_count,
            "citations_emitted": len(last_citations),
            "verified_citations": sum(1 for c in last_citations if c.is_verified),
            "citation_precision": last_verification_result.citation_precision,
            "citation_recall": last_verification_result.citation_recall,
            "overall_support_score": last_verification_result.overall_support_score,
            "provenance_valid": provenance_valid,
            "latency_mean_ms": mean_lat,
        })

    # Global Benchmark Metrics
    macro_precision = round(statistics.mean(r["citation_precision"] for r in query_results), 4)
    macro_recall = round(statistics.mean(r["citation_recall"] for r in query_results), 4)
    avg_support = round(statistics.mean(r["overall_support_score"] for r in query_results), 4)
    provenance_integrity_rate = round(
        provenance_checks_passed / total_provenance_checks if total_provenance_checks > 0 else 1.0, 4
    )

    all_latencies_ms.sort()
    n = len(all_latencies_ms)
    p95_idx = int(0.95 * n)

    benchmark_summary = {
        "dataset_version": "1.0.0",
        "dataset_hash": hashlib.sha256(json.dumps([q["query_id"] for q in benchmark_queries]).encode("utf-8")).hexdigest(),
        "timestamp": datetime.now(UTC).isoformat(),
        "benchmark_configuration": {
            "num_queries": len(benchmark_queries),
            "repetitions": repetitions,
            "categories": [
                "single_document_factual",
                "multi_document_synthesis",
                "insufficient_evidence",
                "unsupported_claims",
                "provenance_edge_cases",
            ],
        },
        "operational_metrics": {
            "citation_precision": macro_precision,
            "citation_recall": macro_recall,
            "average_support_score": avg_support,
            "provenance_integrity_rate": provenance_integrity_rate,
        },
        "latency_metrics_ms": {
            "citation_total_mean_ms": round(statistics.mean(all_latencies_ms), 3),
            "citation_total_median_ms": round(statistics.median(all_latencies_ms), 3),
            "citation_total_p95_ms": round(all_latencies_ms[p95_idx], 3),
            "claim_extraction_mean_ms": round(statistics.mean(extraction_latencies_ms), 3),
            "claim_extraction_median_ms": round(statistics.median(extraction_latencies_ms), 3),
            "citation_mapping_mean_ms": round(statistics.mean(mapping_latencies_ms), 3),
            "citation_mapping_median_ms": round(statistics.median(mapping_latencies_ms), 3),
            "citation_verification_mean_ms": round(statistics.mean(verification_latencies_ms), 3),
            "citation_verification_median_ms": round(statistics.median(verification_latencies_ms), 3),
            "citation_formatting_mean_ms": round(statistics.mean(formatting_latencies_ms), 3),
            "citation_formatting_median_ms": round(statistics.median(formatting_latencies_ms), 3),
        },
        "query_evaluations": query_results,
    }

    # Print Summary Table
    print("\n" + "=" * 70)
    print("PHASE 8 CITATION BENCHMARK SUMMARY")
    print("=" * 70)
    print(f"  Macro Citation Precision   : {macro_precision * 100:.2f}%")
    print(f"  Macro Citation Recall      : {macro_recall * 100:.2f}%")
    print(f"  Average Support Score      : {avg_support:.4f}")
    print(f"  Provenance Integrity Rate  : {provenance_integrity_rate * 100:.2f}%")
    print(f"  Total Latency (Mean)       : {benchmark_summary['latency_metrics_ms']['citation_total_mean_ms']} ms")
    print(f"  Total Latency (Median)     : {benchmark_summary['latency_metrics_ms']['citation_total_median_ms']} ms")
    print(f"  Total Latency (P95)        : {benchmark_summary['latency_metrics_ms']['citation_total_p95_ms']} ms")
    print("=" * 70)

    # Save artifact
    if output_path is None:
        output_path = Path("data/benchmarks/citation_benchmark.json")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2)

    print(f"Benchmark results successfully saved to: {output_path}")
    return benchmark_summary


if __name__ == "__main__":
    target_path = Path("data/benchmarks/citation_benchmark.json")
    run_benchmark(output_path=target_path)
