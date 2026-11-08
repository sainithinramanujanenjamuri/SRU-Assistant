"""Evaluator for generation quality, RAG Triad, and source citations."""

from typing import Sequence

from citations.models import CitationVerificationResult
from evaluation.generation.metrics import (
    compute_answer_relevance,
    compute_completeness,
    compute_context_relevance,
    compute_correctness,
    compute_groundedness,
    compute_unsupported_claim_rate,
)
from evaluation.models import BenchmarkQuery, CitationMetrics, GenerationMetrics
from generation.models import RAGResponse
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK


class GenerationEvaluator:
    """Evaluates RAGResponse generation outputs against benchmark queries."""

    def evaluate_response(
        self,
        response: RAGResponse,
        query: BenchmarkQuery,
    ) -> tuple[GenerationMetrics, CitationMetrics]:
        """Compute generation quality and citation attribution metrics for a single response."""
        is_fallback = (
            response.answer.strip() == INSUFFICIENT_EVIDENCE_FALLBACK
            or not response.is_grounded
        )
        retrieved_chunk_ids = [e.chunk_id for e in response.evidence]

        # Extract verified claims if citation verification was run
        claims = None
        if response.citation_verification:
            claims = response.citation_verification.claims

        groundedness = compute_groundedness(claims, response.answer, is_fallback)
        ans_relevance = compute_answer_relevance(
            query.query, response.answer, query.is_answerable, is_fallback
        )
        ctx_relevance = compute_context_relevance(
            retrieved_chunk_ids, query.expected_chunk_ids
        )
        correctness = compute_correctness(
            response.answer, query.expected_answer, query.is_answerable, is_fallback
        )
        completeness = compute_completeness(
            response.answer, query.expected_entities, query.is_answerable, is_fallback
        )
        unsupported_rate = compute_unsupported_claim_rate(groundedness)

        gen_metrics = GenerationMetrics(
            groundedness=round(groundedness, 4),
            answer_relevance=round(ans_relevance, 4),
            context_relevance=round(ctx_relevance, 4),
            correctness=round(correctness, 4),
            completeness=round(completeness, 4),
            unsupported_claim_rate=round(unsupported_rate, 4),
        )

        # Citation metrics
        cit_prec = 0.0
        cit_rec = 0.0
        cit_comp = 0.0
        ev_supp = 0.0

        if is_fallback:
            # On fallback / unanswerable: having 0 false citations is perfect citation integrity
            cit_prec = 1.0 if len(response.citations) == 0 else 0.0
            cit_rec = 1.0 if len(response.citations) == 0 else 0.0
            cit_comp = 1.0 if len(response.citations) == 0 else 0.0
            ev_supp = 1.0 if len(response.citations) == 0 else 0.0
        elif response.citation_verification:
            cv: CitationVerificationResult = response.citation_verification
            cit_prec = cv.citation_precision
            cit_rec = cv.citation_recall
            ev_supp = cv.overall_support_score
            # Completeness: claims supported with verified citation / total claims
            total_claims = len(cv.claims)
            if total_claims > 0:
                supported_claims = sum(
                    1 for c in cv.claims if c.is_supported and len(c.associated_citation_ids) > 0
                )
                cit_comp = supported_claims / total_claims
            else:
                cit_comp = 1.0
        elif response.citations:
            # Citations emitted without formal verification
            cit_prec = 1.0
            cit_rec = 1.0
            cit_comp = 1.0
            ev_supp = 1.0

        citation_metrics = CitationMetrics(
            citation_precision=round(cit_prec, 4),
            citation_recall=round(cit_rec, 4),
            citation_completeness=round(cit_comp, 4),
            evidence_support=round(ev_supp, 4),
        )

        return gen_metrics, citation_metrics

    def aggregate_metrics(
        self,
        metrics_list: Sequence[tuple[GenerationMetrics, CitationMetrics]],
    ) -> tuple[GenerationMetrics, CitationMetrics]:
        """Compute macro-averages over a dataset of query evaluations."""
        if not metrics_list:
            return GenerationMetrics(), CitationMetrics()

        n = len(metrics_list)
        avg_groundedness = sum(m[0].groundedness for m in metrics_list) / n
        avg_ans_rel = sum(m[0].answer_relevance for m in metrics_list) / n
        avg_ctx_rel = sum(m[0].context_relevance for m in metrics_list) / n
        avg_correctness = sum(m[0].correctness for m in metrics_list) / n
        avg_completeness = sum(m[0].completeness for m in metrics_list) / n
        avg_unsupported = sum(m[0].unsupported_claim_rate for m in metrics_list) / n

        avg_cit_prec = sum(m[1].citation_precision for m in metrics_list) / n
        avg_cit_rec = sum(m[1].citation_recall for m in metrics_list) / n
        avg_cit_comp = sum(m[1].citation_completeness for m in metrics_list) / n
        avg_ev_supp = sum(m[1].evidence_support for m in metrics_list) / n

        macro_gen = GenerationMetrics(
            groundedness=round(avg_groundedness, 4),
            answer_relevance=round(avg_ans_rel, 4),
            context_relevance=round(avg_ctx_rel, 4),
            correctness=round(avg_correctness, 4),
            completeness=round(avg_completeness, 4),
            unsupported_claim_rate=round(avg_unsupported, 4),
        )
        macro_cit = CitationMetrics(
            citation_precision=round(avg_cit_prec, 4),
            citation_recall=round(avg_cit_rec, 4),
            citation_completeness=round(avg_cit_comp, 4),
            evidence_support=round(avg_ev_supp, 4),
        )
        return macro_gen, macro_cit
