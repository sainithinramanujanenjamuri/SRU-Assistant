"""Script to verify live Qwen3.5:4b neural generation, grounding, conflict detection, and citations."""
import sys
import time

# Ensure clean UTF-8 output on Windows
sys.stdout.reconfigure(encoding="utf-8")

from app.api.schemas import QueryRequest
from app.services.query_service import RAGQueryService


def run_live_verification():
    RAGQueryService._instance = None
    service = RAGQueryService.get_instance()

    print(f"Service Generator: {service.generator.model_name} (provider: {service.generator.provider_name})")
    avail, msg = service.generator.is_available()
    print(f"Ollama Availability: {avail} ({msg})")

    if not avail:
        print("Ollama is not available. Please ensure Ollama is running and qwen3.5:4b is pulled.")
        return

    test_scenarios = [
        {
            "name": "Mid-Semester Exam Schedule (SRU Academic Calendar)",
            "query": "When does Mid-Semester Examination I start for B.Tech VII semester?",
        },
        {
            "name": "Credit Registration Limits (SRU Academic Regulations R23)",
            "query": "What is the maximum number of credits a student can register for in a semester under R23 regulations?",
        },
        {
            "name": "Cross-Document / Regulations Query",
            "query": "What are the minimum attendance requirements and what happens if attendance is below 75%?",
        },
        {
            "name": "Unsupported Topic (Safe No-Answer Policy)",
            "query": "What are the hostel mess charges and fee structure for the 2026 academic year?",
        },
    ]

    for scenario in test_scenarios:
        print(f"\n{'='*80}")
        print(f"SCENARIO: {scenario['name']}")
        print(f"QUERY: {scenario['query']}")
        print(f"{'-'*80}")

        t0 = time.perf_counter()
        req = QueryRequest(query=scenario["query"], retrieval_mode="enhanced", verify_citations=True)
        res = service.query(req)
        total_time = time.perf_counter() - t0

        print(f"ANSWER:\n{res.answer}\n")
        print(f"CITED ANSWER:\n{res.cited_answer}\n")
        print(f"Grounding: is_grounded={res.is_grounded}")
        print(f"Latency: total={total_time:.2f}s (pipeline latency dict: {res.latency_ms})")
        print(f"Citations ({len(res.citations)} items):")
        for c in res.citations:
            print(f"  [{c.citation_id}] {c.document_name} ({c.section}) - verified={c.is_verified}")
        if res.verification:
            print(
                f"Verification: Precision={res.verification.citation_precision:.2f}, "
                f"Recall={res.verification.citation_recall:.2f}, "
                f"Unsupported Claims={res.verification.unsupported_claims_count}"
            )


if __name__ == "__main__":
    run_live_verification()

