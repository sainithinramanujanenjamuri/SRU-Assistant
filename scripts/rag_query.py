from __future__ import annotations


import argparse
import sys
from pathlib import Path

# Ensure project root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config.settings import get_settings
from generation.grounding.conflict_detector import ConflictDetector
from generation.grounding.validator import GroundingValidator
from generation.llm.factory import get_generator
from generation.pipeline import BaselineRAGPipeline
from generation.prompts.context_builder import ContextBuilder
from generation.prompts.templates import GroundedPromptTemplate
from retrieval import (
    AcademicQueryAnalyzer,
    BaseRetriever,
    BM25Retriever,
    EnhancedRetriever,
    HybridRetriever,
    MetadataFilter,
    SQLiteVectorStore,
    VectorRetriever,
    get_embedding_model,
    get_reranker,
)


def main() -> None:
    settings = get_settings()

    parser = argparse.ArgumentParser(
        description="Query SR University Academic Documentation via Grounded RAG (Phase 7)",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--query", "-q", type=str, default=None, help="Academic query text to resolve")
    parser.add_argument("--top-k", "-k", type=int, default=settings.retrieval_top_k, help="Number of chunks to return")
    parser.add_argument(
        "--retrieval-mode",
        type=str,
        choices=["dense", "lexical", "hybrid"],
        default=settings.retrieval_mode,
        help="Base candidate retrieval mode",
    )
    parser.add_argument(
        "--fusion-method",
        type=str,
        choices=["rrf", "weighted"],
        default=settings.hybrid_fusion_method,
        help="Rank fusion algorithm for hybrid retrieval",
    )
    # Phase 6 flags
    parser.add_argument(
        "--rerank",
        dest="enable_rerank",
        action="store_true",
        default=None,
        help="Enable re-ranking step",
    )
    parser.add_argument(
        "--no-rerank",
        dest="enable_rerank",
        action="store_false",
        help="Disable re-ranking step (use passthrough/fusion order)",
    )
    parser.add_argument(
        "--reranker-type",
        type=str,
        choices=["deterministic", "transformer", "ollama", "passthrough"],
        default=settings.reranker_type,
        help="Reranker backend provider",
    )
    parser.add_argument(
        "--filter-mode",
        type=str,
        choices=["soft", "hard"],
        default=settings.retrieval_filter_mode,
        help="Institutional metadata filter mode",
    )
    # Phase 7 Grounding & Conflict flags
    parser.add_argument(
        "--strict-grounding",
        dest="strict_grounding",
        action="store_true",
        default=settings.grounding_strict_mode,
        help="Enforce strict grounding: trigger no-answer or safe removal on ungrounded claims",
    )
    parser.add_argument(
        "--prompt-style",
        type=str,
        choices=["default", "academic_rigor", "concise"],
        default=settings.grounded_system_prompt_style,
        help="System prompt grounding style",
    )
    # Phase 8 Citation & Provenance flags
    parser.add_argument(
        "--citation-style",
        type=str,
        choices=["inline_bracket", "source_block", "footnote"],
        default=settings.citation_style,
        help="Phase 8 citation rendering style",
    )
    parser.add_argument(
        "--verify-citations",
        dest="verify_citations",
        action="store_true",
        default=settings.citation_verification_enabled,
        help="Enable deterministic claim-evidence citation verification",
    )
    parser.add_argument(
        "--no-verify-citations",
        dest="verify_citations",
        action="store_false",
        help="Disable citation verification",
    )
    parser.add_argument(
        "--show-conflicts",
        action="store_true",
        default=False,
        help="Display cross-document institutional conflict analysis",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=settings.rag_relevance_threshold,
        help=f"Minimum relevance threshold in [0, 1] (default: {settings.rag_relevance_threshold})",
    )
    parser.add_argument(
        "--db-path",
        type=str,
        default=settings.vectorstore_path,
        help=f"Path to SQLite vector database (default: {settings.vectorstore_path})",
    )
    parser.add_argument(
        "--bm25-path",
        type=str,
        default=str(settings.bm25_index_path),
        help=f"Path to BM25 index (default: {settings.bm25_index_path})",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=settings.llm_provider,
        help=f"Generator provider: deterministic, ollama (default: {settings.llm_provider})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=settings.llm_model,
        help=f"Generator model identifier (default: {settings.llm_model})",
    )
    # Metadata filters
    parser.add_argument("--department", type=str, default=None, help="Filter by department (e.g. CSE)")
    parser.add_argument("--semester", type=str, default=None, help="Filter by semester (e.g. VII)")
    parser.add_argument("--regulation", type=str, default=None, help="Filter by regulation (e.g. R23)")

    args = parser.parse_args()

    # Get query
    query = args.query
    if not query:
        print("=" * 70)
        print("SRU ASSISTANT — GROUNDED RAG QUERY INTERFACE (PHASE 8)")
        print("=" * 70)
        try:
            query = input("Enter your academic query: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting.")
            sys.exit(0)

    if not query:
        print("Empty query provided. Exiting.")
        sys.exit(1)

    # Initialize components
    try:
        embedding_model = get_embedding_model()
        vector_store = SQLiteVectorStore(db_path=args.db_path)
        dense_retriever = VectorRetriever(embedding_model=embedding_model, vector_store=vector_store)

        if args.retrieval_mode == "dense":
            base_retriever: BaseRetriever = dense_retriever
        elif args.retrieval_mode == "lexical":
            bm25_index_file = Path(args.bm25_path)
            if not bm25_index_file.exists():
                print(
                    f"Warning: BM25 index file not found at '{args.bm25_path}'. "
                    "Falling back to dense vector retriever."
                )
                base_retriever = dense_retriever
            else:
                base_retriever = BM25Retriever.from_file(index_path=bm25_index_file)
        else:  # hybrid
            bm25_index_file = Path(args.bm25_path)
            if not bm25_index_file.exists():
                print(
                    f"Warning: BM25 index file not found at '{args.bm25_path}'. "
                    "Falling back to dense vector retriever."
                )
                base_retriever = dense_retriever
            else:
                lexical_retriever = BM25Retriever.from_file(index_path=bm25_index_file)
                base_retriever = HybridRetriever(
                    dense_retriever=dense_retriever,
                    lexical_retriever=lexical_retriever,
                    fusion_method=args.fusion_method,
                )

        # Apply Phase 6 Enhanced Retriever if re-ranking, query analysis, or metadata filters are active
        should_use_enhanced = (
            args.enable_rerank is True
            or (args.enable_rerank is None and settings.retrieval_reranking_enabled)
            or settings.query_analysis_enabled
            or args.filter_mode != "soft"
        )
        if should_use_enhanced:
            should_rerank = (
                args.enable_rerank if args.enable_rerank is not None else settings.retrieval_reranking_enabled
            )
            reranker = get_reranker(method=args.reranker_type)
            retriever: BaseRetriever = EnhancedRetriever(
                hybrid_retriever=base_retriever,
                query_analyzer=AcademicQueryAnalyzer() if settings.query_analysis_enabled else None,
                metadata_filter=MetadataFilter(mode=args.filter_mode),
                reranker=reranker,
                candidate_k=settings.reranker_candidate_k,
                filter_mode=args.filter_mode,
                enable_reranking=should_rerank,
            )
        else:
            retriever = base_retriever

        # Context Builder with relevance threshold
        context_builder = ContextBuilder(
            relevance_threshold=args.threshold,
            max_context_tokens=settings.rag_context_max_tokens,
        )

        # Grounded Generator (Phase 7 / Phase 4)
        generator = get_generator(provider=args.provider, model=args.model)

        # Prompt template with specified style
        prompt_template = GroundedPromptTemplate(style=args.prompt_style)

        # Conflict Detector and Grounding Validator
        conflict_detector = ConflictDetector()
        grounding_validator = GroundingValidator(strict_mode=args.strict_grounding)

        pipeline = BaselineRAGPipeline(
            retriever=retriever,
            generator=generator,
            context_builder=context_builder,
            prompt_template=prompt_template,
            conflict_detector=conflict_detector,
            grounding_validator=grounding_validator,
        )
    except Exception as e:
        print(f"Initialization failed: {e}", file=sys.stderr)
        sys.exit(1)

    # Build filters
    filters = {}
    if args.department:
        filters["department"] = args.department
    if args.semester:
        filters["semester"] = args.semester
    if args.regulation:
        filters["regulation"] = args.regulation

    print("\n" + "=" * 70)
    print(f"QUESTION: {query}")
    if filters:
        print(f"FILTERS : {filters}")
    print(f"MODE    : {getattr(retriever, 'retrieval_mode', args.retrieval_mode).upper()}")
    print(f"ENGINE  : {generator.model_name} (Provider: {generator.provider_name}, LLM: {generator.is_llm})")
    print(f"STYLE   : {args.prompt_style} (Strict Grounding: {args.strict_grounding})")
    print(f"CITATION: {args.citation_style} (Verification: {args.verify_citations})")
    print("-" * 70)

    try:
        response = pipeline.answer_query(
            query=query,
            top_k=args.top_k,
            filters=filters or None,
            citation_style=args.citation_style,
            verify_citations=args.verify_citations,
        )
    except Exception as e:
        print(f"Query resolution failed: {e}", file=sys.stderr)
        sys.exit(1)

    print("ANSWER:")
    print(response.answer)
    print("\n" + "-" * 70)

    if response.cited_answer and response.cited_answer != response.answer:
        print(f"CITED ANSWER (Style: {args.citation_style}):")
        print(response.cited_answer)
        print("\n" + "-" * 70)

    # Conflict Diagnostics
    if response.conflict_report and response.conflict_report.has_conflict:
        cr = response.conflict_report
        print("INSTITUTIONAL CONFLICT DETECTED:")
        print(f"  Conflict Type: {cr.conflict_type}")
        print(f"  Conflicting Sources: {', '.join(cr.conflicting_sources)}")
        for d in cr.details:
            print(f"    - {d}")
        print("-" * 70)
    elif args.show_conflicts:
        print("INSTITUTIONAL CONFLICTS: None detected across retrieved evidence.")
        print("-" * 70)

    print(f"CITATIONS ({len(response.citations)} emitted):")
    if response.citations:
        for cit in response.citations:
            v_status = "VERIFIED" if cit.is_verified else "UNVERIFIED"
            score_str = f"{cit.support_score:.4f}" if cit.support_score is not None else "N/A"
            print(f"  [{cit.citation_id}] {cit.source}")
            print(f"      Document: {cit.document_name} | Page: {cit.page_info} | Section: {cit.section}")
            print(f"      Chunk ID: {cit.chunk_id} | Verification: {v_status} | Support Score: {score_str}")
    else:
        print("  [No citations emitted]")

    if response.citation_verification:
        cv = response.citation_verification
        print("-" * 70)
        print("CITATION VERIFICATION AUDIT:")
        print(f"  Fully Supported     : {cv.is_fully_supported}")
        print(f"  Citation Precision  : {cv.citation_precision:.4f}")
        print(f"  Citation Recall     : {cv.citation_recall:.4f}")
        print(f"  Overall Support     : {cv.overall_support_score:.4f}")
        if cv.unsupported_claims:
            print("  Unsupported Claims  :")
            for uc in cv.unsupported_claims:
                print(f"    - {uc}")
        if cv.unverified_citations:
            print(f"  Unverified Citations: {cv.unverified_citations}")

    print("-" * 70)
    print(f"ATTRIBUTED EVIDENCE ({len(response.evidence)} sources used):")
    if response.evidence:
        for idx, ev in enumerate(response.evidence, start=1):
            score_info = f"Score: {ev.score:.4f}"
            if ev.rerank_score is not None:
                rank_str = f"Rank: {ev.rerank_rank}" if ev.rerank_rank is not None else ""
                delta_str = f"(delta: {ev.initial_rank - ev.rerank_rank})" if (ev.initial_rank and ev.rerank_rank) else ""
                score_info = f"Rerank Score: {ev.rerank_score:.4f} [{rank_str} {delta_str}]"
            elif ev.dense_score is not None or ev.lexical_score is not None:
                parts = []
                if ev.dense_score is not None:
                    parts.append(f"Dense: {ev.dense_score:.4f}")
                if ev.lexical_score is not None:
                    parts.append(f"Lexical: {ev.lexical_score:.4f}")
                score_info += f" ({', '.join(parts)})"

            print(f"  [{idx}] {ev.document_name} | {ev.page_info} | Section: {ev.section_path}")
            print(f"      Chunk ID: {ev.chunk_id} | {score_info}")
    else:
        print("  [No evidence survived relevance filtering]")

    print("-" * 70)
    print("OBSERVABILITY METRICS:")
    print(f"  Retrieval Mode      : {response.retrieval_mode}")
    print(f"  Retrieval Latency   : {response.retrieval_latency_ms:.2f} ms")

    if response.enhanced_meta:
        em = response.enhanced_meta
        print(f"    - Query Analysis  : {em.get('query_analysis_latency_ms', 0):.2f} ms")
        print(f"    - Candidate Pool  : {em.get('candidate_retrieval_latency_ms', 0):.2f} ms (Count: {em.get('initial_candidate_count', 0)})")
        print(f"    - Metadata Filter : {em.get('metadata_filter_latency_ms', 0):.2f} ms (Surviving: {em.get('post_filter_count', 0)}, Mode: {em.get('filter_mode', 'none')})")
        print(f"    - Re-ranking      : {em.get('reranking_latency_ms', 0):.2f} ms (Model: {em.get('reranker_model', 'none')}, Moved Up: {em.get('moved_up_count', 0)}, Down: {em.get('moved_down_count', 0)})")
    elif response.hybrid_meta:
        hm = response.hybrid_meta
        print(f"    - Dense Latency   : {hm.get('dense_latency_ms', 0):.2f} ms (Hits: {hm.get('dense_candidates_retrieved', 0)})")
        print(f"    - Lexical Latency : {hm.get('lexical_latency_ms', 0):.2f} ms (Hits: {hm.get('lexical_candidates_retrieved', 0)})")
        print(f"    - Fusion Latency  : {hm.get('fusion_latency_ms', 0):.2f} ms (Fused: {hm.get('fused_candidates_count', 0)})")

    print(f"  Context Assembly    : {response.context_latency_ms:.2f} ms")
    print(f"  Conflict Detection  : {response.conflict_latency_ms:.2f} ms")
    print(f"  Generation Latency  : {response.generation_latency_ms:.2f} ms")
    print(f"  Grounding Audit     : {response.grounding_latency_ms:.2f} ms")
    print(f"  Citation Processing : {response.citation_latency_ms:.2f} ms")
    print(f"  Total Pipeline Time : {response.total_latency_ms:.2f} ms")

    if response.grounding_validation:
        gv = response.grounding_validation
        print("  Grounding Audit Details:")
        print(f"    - Grounded Status : {gv.is_grounded}")
        print(f"    - Faithfulness    : {gv.faithfulness_score:.4f} (Approximation in [0, 1])")
        print(f"    - Entity Coverage : {gv.entity_coverage:.4f}")
        print(f"    - Token Overlap   : {gv.token_overlap:.4f}")
        print(f"    - Stmt Support    : {gv.statement_support:.4f}")
        if gv.ungrounded_entities:
            print(f"    - Ungrounded Ent  : {gv.ungrounded_entities}")
        if gv.remediation_applied:
            print("    - Remediation     : Remediation Applied (Strict Mode Active)")

    print("=" * 70)


if __name__ == "__main__":
    main()
