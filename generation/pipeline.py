"""Baseline RAG Pipeline connecting semantic vector retrieval, context budgeting, conflict detection, and grounded generation."""
from __future__ import annotations


import time
from typing import TYPE_CHECKING, Any

from app.config.settings import get_settings
from generation.grounding.conflict_detector import ConflictDetector
from generation.grounding.validator import GroundingValidator
from generation.llm.base import BaseGenerator
from generation.models import (
    GenerationError,
    RAGResponse,
)
from generation.prompts.context_builder import ContextBuilder
from generation.prompts.templates import (
    INSUFFICIENT_EVIDENCE_FALLBACK,
    GroundedPromptTemplate,
)
from retrieval.base import BaseRetriever

if TYPE_CHECKING:
    from citations.citation_mapper import CitationMapper
    from citations.citation_verifier import CitationVerifier
    from citations.claim_extractor import ClaimExtractor
    from citations.formatter import CitationFormatter


class BaselineRAGPipeline:
    """End-to-end Grounded RAG Pipeline (Phases 4–8).


    Orchestrates:
    1. Query validation.
    2. Candidate retrieval via BaseRetriever (VectorRetriever, BM25Retriever, HybridRetriever, or EnhancedRetriever).
    3. Relevance filtering and token-budgeted context construction.
    4. Cross-document institutional conflict detection (Phase 7).
    5. Safe no-answer short-circuiting on insufficient evidence.
    6. Grounded prompt generation and answer synthesis.
    7. Post-generation grounding validation and strict/non-strict remediation (Phase 7).
    8. Claim extraction and proposition decomposition (Phase 8).
    9. Claim-to-evidence alignment and granular provenance mapping (Phase 8).
    10. Deterministic citation verification and factual audit (Phase 8).
    11. Multi-style citation rendering and observable telemetry (Phase 8).
    """

    def __init__(
        self,
        retriever: BaseRetriever,
        generator: BaseGenerator,
        context_builder: ContextBuilder | None = None,
        prompt_template: GroundedPromptTemplate | None = None,
        conflict_detector: ConflictDetector | None = None,
        grounding_validator: GroundingValidator | None = None,
        claim_extractor: "ClaimExtractor | None" = None,
        citation_mapper: "CitationMapper | None" = None,
        citation_verifier: "CitationVerifier | None" = None,
        citation_formatter: "CitationFormatter | None" = None,
    ):
        settings = get_settings()
        self.retriever = retriever
        self.generator = generator
        self.context_builder = context_builder or ContextBuilder()
        self.prompt_template = prompt_template or GroundedPromptTemplate(style=settings.grounded_system_prompt_style)
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.grounding_validator = grounding_validator or GroundingValidator()

        # Lazy import of citation components to prevent circular imports during module loading
        if claim_extractor is None:
            from citations.claim_extractor import ClaimExtractor
            self.claim_extractor = ClaimExtractor()
        else:
            self.claim_extractor = claim_extractor

        if citation_mapper is None:
            from citations.citation_mapper import CitationMapper
            self.citation_mapper = CitationMapper()
        else:
            self.citation_mapper = citation_mapper

        if citation_verifier is None:
            from citations.citation_verifier import CitationVerifier
            self.citation_verifier = CitationVerifier(
                min_support_score=settings.citation_min_support_score,
                require_exact_entities=settings.citation_require_exact_entities,
            )
        else:
            self.citation_verifier = citation_verifier

        if citation_formatter is None:
            from citations.formatter import CitationFormatter
            self.citation_formatter = CitationFormatter()
        else:
            self.citation_formatter = citation_formatter

        self._conflict_detection_enabled = settings.conflict_detection_enabled
        self._grounding_validation_enabled = settings.grounding_validation_enabled
        self._citation_verification_enabled = settings.citation_verification_enabled
        self._citation_style = settings.citation_style

    def answer_query(
        self,
        query: str,
        top_k: int = 5,
        filters: dict[str, Any] | None = None,
        citation_style: str | None = None,
        verify_citations: bool | None = None,
    ) -> RAGResponse:
        """Answer a student academic query using grounded evidence from the university knowledge base."""
        t_total_0 = time.perf_counter()

        if not isinstance(query, str) or not query.strip():
            raise ValueError("Query string cannot be empty or whitespace-only")
        if top_k <= 0:
            raise ValueError(f"top_k must be a positive integer, got {top_k}")

        cleaned_query = query.strip()

        # Step 1: Candidate retrieval
        t_ret_0 = time.perf_counter()
        search_results = self.retriever.search(
            query=cleaned_query,
            top_k=top_k,
            filters=filters,
        )
        retrieval_ms = (time.perf_counter() - t_ret_0) * 1000.0

        # Step 2: Context building and relevance threshold filtering
        t_ctx_0 = time.perf_counter()
        context = self.context_builder.build_context(
            query=cleaned_query,
            search_results=search_results,
        )
        context_ms = (time.perf_counter() - t_ctx_0) * 1000.0

        # Determine retrieval mode and diagnostics
        hybrid_meta = None
        enhanced_meta = None
        if hasattr(self.retriever, "last_meta") and self.retriever.last_meta is not None:
            last_meta = self.retriever.last_meta
            if hasattr(last_meta, "actual_mode"):
                retrieval_mode = last_meta.actual_mode
                hybrid_meta = last_meta.model_dump()
            elif hasattr(last_meta, "reranker_name"):
                retrieval_mode = getattr(last_meta, "retrieval_mode", "enhanced")
                enhanced_meta = last_meta.model_dump()
            else:
                retrieval_mode = getattr(self.retriever, "retrieval_mode", "dense")
        else:
            retrieval_mode = getattr(self.retriever, "retrieval_mode", "dense")

        # Step 3: Conflict detection across surviving evidence (Phase 7)
        conflict_report = None
        conflict_ms = 0.0
        if self._conflict_detection_enabled and context.has_sufficient_evidence:
            t_conf_0 = time.perf_counter()
            conflict_report = self.conflict_detector.detect_conflicts(context.evidence_items)
            conflict_ms = (time.perf_counter() - t_conf_0) * 1000.0

        # Step 4: No-Answer Policy on insufficient evidence
        if not context.has_sufficient_evidence:
            total_ms = (time.perf_counter() - t_total_0) * 1000.0
            return RAGResponse(
                query=cleaned_query,
                answer=INSUFFICIENT_EVIDENCE_FALLBACK,
                evidence=[],
                is_grounded=False,
                generator_name=self.generator.model_name,
                provider_name=self.generator.provider_name,
                is_llm=self.generator.is_llm,
                retrieval_mode=retrieval_mode,
                retrieval_latency_ms=round(retrieval_ms, 2),
                context_latency_ms=round(context_ms, 2),
                conflict_latency_ms=0.0,
                generation_latency_ms=0.0,
                grounding_latency_ms=0.0,
                citation_latency_ms=0.0,
                total_latency_ms=round(total_ms, 2),
                hybrid_meta=hybrid_meta,
                enhanced_meta=enhanced_meta,
                grounding_validation=None,
                conflict_report=None,
                citations=[],
                citation_verification=None,
                cited_answer=INSUFFICIENT_EVIDENCE_FALLBACK,
            )

        # Step 5: Prompt rendering with conflict notice if present
        full_prompt = self.prompt_template.render_full_prompt(context, conflict_report=conflict_report)
        system_prompt = self.prompt_template.render_system_prompt()

        # Step 6: Answer generation
        t_gen_0 = time.perf_counter()
        gen_response = self.generator.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
        )
        generation_ms = (time.perf_counter() - t_gen_0) * 1000.0

        # Step 7: Generator output validation
        raw_answer_text = gen_response.text.strip()
        if not raw_answer_text:
            raise GenerationError("Generator returned an empty answer text.")

        # Step 8: Grounding Validation & Remediation (Phase 7)
        grounding_report = None
        grounding_ms = 0.0
        final_answer = raw_answer_text

        if self._grounding_validation_enabled:
            t_grd_0 = time.perf_counter()
            grounding_report, final_answer = self.grounding_validator.validate(
                answer=raw_answer_text,
                evidence_items=context.evidence_items,
                conflict_report=conflict_report,
            )
            grounding_ms = (time.perf_counter() - t_grd_0) * 1000.0

        is_fallback = final_answer == INSUFFICIENT_EVIDENCE_FALLBACK
        is_grounded = (not is_fallback) and (grounding_report.is_grounded if grounding_report else True)

        # Step 9: Citation Extraction, Mapping, Verification & Rendering (Phase 8)
        citations: list = []
        citation_verification = None
        citation_ms = 0.0
        cited_answer = final_answer

        style_to_use = citation_style or self._citation_style
        should_verify = (
            self._citation_verification_enabled if verify_citations is None else verify_citations
        )

        if not is_fallback and context.evidence_items:
            t_cit_0 = time.perf_counter()
            # 1. Claim extraction
            claims = self.claim_extractor.extract_claims(final_answer)

            # 2. Citation mapping against generation evidence
            mapped_claims, citations = self.citation_mapper.map_claims_to_evidence(
                claims=claims,
                evidence_items=context.evidence_items,
            )

            # 3. Citation verification if enabled
            if should_verify:
                citation_verification = self.citation_verifier.verify_citations(
                    claims=mapped_claims,
                    citations=citations,
                    evidence_items=context.evidence_items,
                )
                citations = citation_verification.citations
                mapped_claims = citation_verification.claims

            # 4. Render cited_answer
            cited_answer = self.citation_formatter.format(
                answer=final_answer,
                citations=citations,
                claims=mapped_claims,
                style=style_to_use,  # type: ignore[arg-type]
            )
            citation_ms = (time.perf_counter() - t_cit_0) * 1000.0

        total_ms = (time.perf_counter() - t_total_0) * 1000.0

        return RAGResponse(
            query=cleaned_query,
            answer=final_answer,
            evidence=context.evidence_items,
            is_grounded=is_grounded,
            generator_name=gen_response.model_name,
            provider_name=gen_response.provider_name,
            is_llm=gen_response.is_llm,
            retrieval_mode=retrieval_mode,
            retrieval_latency_ms=round(retrieval_ms, 2),
            context_latency_ms=round(context_ms, 2),
            conflict_latency_ms=round(conflict_ms, 2),
            generation_latency_ms=round(generation_ms, 2),
            grounding_latency_ms=round(grounding_ms, 2),
            citation_latency_ms=round(citation_ms, 2),
            total_latency_ms=round(total_ms, 2),
            hybrid_meta=hybrid_meta,
            enhanced_meta=enhanced_meta,
            grounding_validation=grounding_report,
            conflict_report=conflict_report,
            citations=citations,
            citation_verification=citation_verification,
            cited_answer=cited_answer,
        )
