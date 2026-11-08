"""Application service for orchestrating RAG queries and document management (Phase 10)."""

from __future__ import annotations

import json
import time
from pathlib import Path

from app.api.schemas import (
    CitationDetail,
    DocumentSummary,
    HealthResponse,
    QueryRequest,
    QueryResponse,
    VerificationSummary,
)
from app.config.settings import get_settings
from app.security import (
    DocumentGuard,
    DocumentValidationResult,
    ObservabilityLogger,
    QueryGuard,
    RequestTelemetry,
    generate_request_id,
)
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


class IngestionStageError(RuntimeError):
    """Raised when document ingestion or indexing fails at a specific pipeline stage."""

    def __init__(self, stage: str, message: str, original_error: Exception | None = None) -> None:
        super().__init__(f"Ingestion failed at stage '{stage}': {message}")
        self.stage = stage
        self.original_error = original_error


class RAGQueryService:
    """Singleton service maintaining cached retrievers, generators, and RAG pipelines."""

    _instance: RAGQueryService | None = None

    def __init__(self) -> None:
        self.settings = get_settings()
        self.query_guard = QueryGuard(min_length=2, max_length=1000)
        self.document_guard = DocumentGuard()
        self.telemetry_logger = ObservabilityLogger()
        self._init_components()

    @classmethod
    def get_instance(cls) -> RAGQueryService:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _init_components(self) -> None:
        """Initialize and cache retriever, database connections, and pipeline components."""
        settings = self.settings

        # 1. Embedding Model
        self.embedding_model = get_embedding_model(
            provider=settings.embedding_provider,
            model_name=settings.embedding_model,
            dimension=settings.embedding_dimension,
        )

        # 2. Vector Store
        self.vector_store = SQLiteVectorStore(db_path=settings.vectorstore_path)

        # 3. Dense Retriever
        self.dense_retriever = VectorRetriever(
            embedding_model=self.embedding_model,
            vector_store=self.vector_store,
        )

        # 4. Lexical Retriever (BM25)
        bm25_path = Path(settings.bm25_index_path)
        if bm25_path.exists():
            self.bm25_retriever = BM25Retriever.from_file(index_path=bm25_path)
        else:
            self.bm25_retriever = BM25Retriever()

        # 5. Hybrid Retriever
        self.hybrid_retriever = HybridRetriever(
            dense_retriever=self.dense_retriever,
            lexical_retriever=self.bm25_retriever,
            fusion_method=settings.hybrid_fusion_method,
        )

        # 6. Re-ranker & Query Analyzer
        self.reranker = get_reranker(method=settings.reranker_type)
        self.query_analyzer = AcademicQueryAnalyzer()
        self.metadata_filter = MetadataFilter(mode=settings.retrieval_filter_mode)

        # 7. Enhanced Retriever (Hybrid + Filter + Rerank)
        self.enhanced_retriever = EnhancedRetriever(
            hybrid_retriever=self.hybrid_retriever,
            reranker=self.reranker,
            query_analyzer=self.query_analyzer,
            metadata_filter=self.metadata_filter,
            candidate_k=settings.reranker_candidate_k,
            filter_mode=settings.retrieval_filter_mode,
        )

        # 8. Generator
        self.generator = get_generator(
            provider=settings.llm_provider,
            model=settings.llm_model,
            base_url=settings.llm_api_base,
            timeout_seconds=settings.llm_timeout_seconds,
            temperature=settings.llm_temperature,
            max_tokens=settings.llm_max_tokens,
            top_p=getattr(settings, "llm_top_p", None),
        )

        # 9. Context Builder & Grounding Modules
        self.context_builder = ContextBuilder(
            max_context_tokens=settings.rag_context_max_tokens,
            relevance_threshold=settings.rag_relevance_threshold,
        )
        self.prompt_template = GroundedPromptTemplate(style=settings.grounded_system_prompt_style)
        self.conflict_detector = ConflictDetector()
        self.grounding_validator = GroundingValidator()

        # 10. Default Pipeline
        self.pipeline = BaselineRAGPipeline(
            retriever=self.enhanced_retriever,
            generator=self.generator,
            context_builder=self.context_builder,
            prompt_template=self.prompt_template,
            conflict_detector=self.conflict_detector,
            grounding_validator=self.grounding_validator,
        )

    def _get_retriever_for_mode(self, mode: str) -> BaseRetriever:
        m = mode.lower().strip()
        if m == "dense":
            return self.dense_retriever
        elif m == "lexical":
            return self.bm25_retriever
        elif m == "hybrid":
            return self.hybrid_retriever
        return self.enhanced_retriever

    def query(self, req: QueryRequest) -> QueryResponse:
        """Execute grounded RAG query resolution with Phase 11 safety and telemetry."""
        request_id = generate_request_id()
        start_ts = time.time()

        # 1. Query Safety Inspection
        guard_result = self.query_guard.inspect_query(req.query)
        if not guard_result.is_safe:
            # Safe refusal response on prompt injection or malicious pattern
            duration_ms = round((time.time() - start_ts) * 1000, 2)
            telemetry = RequestTelemetry(
                request_id=request_id,
                query_length=len(req.query),
                retrieval_mode=req.retrieval_mode,
                model_name=self.generator.model_name,
                retrieval_count=0,
                citation_count=0,
                is_grounded=True,
                has_conflicts=False,
                latency_breakdown_ms={"total": duration_ms},
                total_latency_ms=duration_ms,
                status_code=400,
                threat_detected=guard_result.threat_type,
                error_message=guard_result.details,
            )
            self.telemetry_logger.record_query(telemetry)

            refusal_ans = guard_result.refusal_message or "Request refused by security policy."
            return QueryResponse(
                request_id=request_id,
                query=guard_result.sanitized_query,
                answer=refusal_ans,
                cited_answer=refusal_ans,
                citations=[],
                verification=VerificationSummary(
                    is_fully_supported=True,
                    citation_precision=1.0,
                    citation_recall=1.0,
                    overall_support_score=1.0,
                    unsupported_claims_count=0,
                ),
                is_grounded=True,
                has_conflicts=False,
                conflict_notes=[],
                latency_ms={"total": duration_ms},
                engine_info={
                    "provider": self.generator.provider_name,
                    "model": self.generator.model_name,
                    "is_llm": self.generator.is_llm,
                    "retrieval_mode": req.retrieval_mode,
                    "security_status": "refused",
                },
            )

        # 2. Conversational Intent (Greetings & University Identity)
        if guard_result.is_conversational:
            duration_ms = round((time.time() - start_ts) * 1000, 2)
            conv_ans = guard_result.conversational_response or "Hello! I am SRU Assistant."
            return QueryResponse(
                request_id=request_id,
                query=guard_result.sanitized_query,
                answer=conv_ans,
                cited_answer=conv_ans,
                citations=[],
                verification=VerificationSummary(
                    is_fully_supported=True,
                    citation_precision=1.0,
                    citation_recall=1.0,
                    overall_support_score=1.0,
                    unsupported_claims_count=0,
                ),
                is_grounded=True,
                has_conflicts=False,
                conflict_notes=[],
                latency_ms={"total": duration_ms},
                engine_info={
                    "provider": "conversational_assistant",
                    "model": "sru-academic-agent",
                    "is_llm": True,
                    "retrieval_mode": req.retrieval_mode,
                    "intent": "conversational",
                },
            )

        # 3. Execute RAG pipeline with sanitized query
        retriever = self._get_retriever_for_mode(req.retrieval_mode)


        pipeline = BaselineRAGPipeline(
            retriever=retriever,
            generator=self.generator,
            context_builder=self.context_builder,
            prompt_template=self.prompt_template,
            conflict_detector=self.conflict_detector,
            grounding_validator=self.grounding_validator,
        )

        raw_resp = pipeline.answer_query(
            query=guard_result.sanitized_query,
            top_k=req.top_k,
            citation_style=req.citation_style,
            verify_citations=req.verify_citations,
        )

        # Map citations to schema
        citations_list: list[CitationDetail] = []
        if raw_resp.citations:
            for c in raw_resp.citations:
                citations_list.append(
                    CitationDetail(
                        citation_id=c.citation_id,
                        document_name=c.document_name,
                        page=c.page,
                        page_info=c.page_info,
                        section=c.section,
                        source_label=c.source,
                        chunk_id=c.chunk_id,
                        claim_text=c.claim_text,
                        is_verified=c.is_verified,
                        support_score=c.support_score,
                    )
                )

        # Map verification summary
        v_summary = VerificationSummary(
            is_fully_supported=True,
            citation_precision=1.0,
            citation_recall=1.0,
            overall_support_score=1.0,
            unsupported_claims_count=0,
        )
        if raw_resp.citation_verification:
            cv = raw_resp.citation_verification
            v_summary = VerificationSummary(
                is_fully_supported=cv.is_fully_supported,
                citation_precision=round(cv.citation_precision, 4),
                citation_recall=round(cv.citation_recall, 4),
                overall_support_score=round(cv.overall_support_score, 4),
                unsupported_claims_count=len(cv.unsupported_claims),
            )

        # Check conflicts
        has_conflicts = False
        conflict_notes: list[str] = []
        if raw_resp.conflict_report and raw_resp.conflict_report.has_conflict:
            has_conflicts = True
            conflict_notes = raw_resp.conflict_report.details or [
                f"Discrepancy detected across sources: {', '.join(raw_resp.conflict_report.conflicting_sources)}"
            ]

        # Grounding status
        is_grounded = True
        if raw_resp.grounding_validation:
            is_grounded = raw_resp.grounding_validation.is_grounded

        latency_dict = {
            "retrieval": round(raw_resp.retrieval_latency_ms, 2),
            "context": round(raw_resp.context_latency_ms, 2),
            "conflict": round(raw_resp.conflict_latency_ms, 2),
            "generation": round(raw_resp.generation_latency_ms, 2),
            "grounding": round(raw_resp.grounding_latency_ms, 2),
            "citation": round(raw_resp.citation_latency_ms, 2),
            "total": round(raw_resp.total_latency_ms, 2),
        }

        # 3. Observability telemetry logging
        retrieved_doc_names = list({c.document_name for c in citations_list if c.document_name})
        telemetry = RequestTelemetry(
            request_id=request_id,
            query_length=len(req.query),
            retrieval_mode=req.retrieval_mode,
            model_name=self.generator.model_name,
            retrieval_count=len(raw_resp.retrieved_chunks) if hasattr(raw_resp, "retrieved_chunks") else len(citations_list),
            retrieved_documents=retrieved_doc_names,
            citation_count=len(citations_list),
            is_grounded=is_grounded,
            has_conflicts=has_conflicts,
            latency_breakdown_ms=latency_dict,
            total_latency_ms=latency_dict["total"],
            status_code=200,
        )
        self.telemetry_logger.record_query(telemetry)

        return QueryResponse(
            request_id=request_id,
            query=raw_resp.query,
            answer=raw_resp.answer,
            cited_answer=raw_resp.cited_answer or raw_resp.answer,
            citations=citations_list,
            verification=v_summary,
            is_grounded=is_grounded,
            has_conflicts=has_conflicts,
            conflict_notes=conflict_notes,
            latency_ms=latency_dict,
            engine_info={
                "provider": self.generator.provider_name,
                "model": self.generator.model_name,
                "is_llm": self.generator.is_llm,
                "retrieval_mode": req.retrieval_mode,
            },
        )

    def validate_and_save_document(self, filename: str, content: bytes) -> DocumentValidationResult:
        """Validate an uploaded document through DocumentGuard and persist to documents/raw/."""
        result = self.document_guard.validate_file_content(filename, content)
        if result.is_valid and not result.is_duplicate:
            raw_dir = Path(self.settings.raw_documents_dir)
            raw_dir.mkdir(parents=True, exist_ok=True)
            target_path = raw_dir / result.safe_filename
            with open(target_path, "wb") as f:
                f.write(content)
            self.document_guard.register_known_hash(result.sha256_hash)
        return result

    def ingest_and_index_file(self, file_path: Path) -> dict[str, Any]:
        """Process, chunk, and index an institutional document with transactional rollback on failure."""
        from ingestion.chunking.pipeline import ChunkingPipeline
        from ingestion.pipeline import DocumentPipeline
        from retrieval.lexical.indexer import BM25Indexer
        from retrieval.vectorstore.indexer import VectorIndexer

        proc_path: Path | None = None
        chunks_path: Path | None = None
        inserted_chunk_ids: list[str] = []
        bm25_indexed_chunk_ids: list[str] = []

        try:
            # Stage 1: Document processing (load, clean, structure, metadata)
            try:
                doc_pipeline = DocumentPipeline()
                processed_doc = doc_pipeline.process_file(file_path)
                proc_dir = Path(self.settings.processed_documents_dir)
                proc_dir.mkdir(parents=True, exist_ok=True)
                proc_path = proc_dir / f"{processed_doc.document_id}.json"
                processed_doc.save_to_file(proc_path)
            except Exception as e:
                raise IngestionStageError("document_processing", str(e), e) from e

            # Stage 2: Chunking pipeline (structure-aware chunking)
            try:
                chunking_pipeline = ChunkingPipeline()
                chunk_dataset = chunking_pipeline.chunk_processed_document(processed_doc)
                chunks_dir = Path(self.settings.chunks_dir)
                chunks_dir.mkdir(parents=True, exist_ok=True)
                chunks_path = chunks_dir / f"{processed_doc.document_id}_chunks.json"
                chunk_dataset.save_to_file(chunks_path)
            except Exception as e:
                raise IngestionStageError("chunking", str(e), e) from e

            # Stage 3: Dense vector indexing
            try:
                vec_indexer = VectorIndexer(
                    embedding_model=self.embedding_model,
                    vector_store=self.vector_store,
                )
                inserted_chunk_ids = [c.chunk_id for c in chunk_dataset.chunks]
                vec_report = vec_indexer.index_chunks(chunk_dataset.chunks)
            except Exception as e:
                raise IngestionStageError("vector_indexing", str(e), e) from e

            # Stage 4: Lexical BM25 indexing (incremental update)
            try:
                bm25_indexer = BM25Indexer(
                    index=self.bm25_retriever.index,
                    index_path=self.settings.bm25_index_path,
                )
                bm25_indexed_chunk_ids = [c.chunk_id for c in chunk_dataset.chunks]
                bm25_report = bm25_indexer.index_chunks(chunk_dataset.chunks, prune_missing=False)
                self.bm25_retriever.index.save(self.settings.bm25_index_path)
            except Exception as e:
                raise IngestionStageError("bm25_indexing", str(e), e) from e

            return {
                "document_id": processed_doc.document_id,
                "filename": file_path.name,
                "chunks_count": len(chunk_dataset.chunks),
                "vector_indexed": vec_report.chunks_indexed,
                "bm25_indexed": bm25_report.chunks_indexed,
            }

        except Exception as err:
            # === TRANSACTIONAL ROLLBACK TO PRESERVE DUAL-STORE SYNCHRONIZATION ===
            # Rollback BM25 in-memory & on-disk
            if bm25_indexed_chunk_ids:
                try:
                    for cid in bm25_indexed_chunk_ids:
                        self.bm25_retriever.index.remove_chunk(cid)
                    self.bm25_retriever.index.save(self.settings.bm25_index_path)
                except Exception:
                    pass

            # Rollback SQLite vector records
            if inserted_chunk_ids:
                try:
                    self.vector_store.delete_records(inserted_chunk_ids)
                except Exception:
                    pass

            # Rollback chunks JSON file (prevents phantom catalog entries in get_documents)
            if chunks_path and chunks_path.exists():
                try:
                    chunks_path.unlink()
                except Exception:
                    pass

            # Rollback processed intermediate JSON file
            if proc_path and proc_path.exists():
                try:
                    proc_path.unlink()
                except Exception:
                    pass

            raise err


    def get_documents(self) -> list[DocumentSummary]:
        """Fetch summary of indexed university documents."""
        docs_summary: list[DocumentSummary] = []
        chunks_dir = Path(self.settings.chunks_dir)
        if chunks_dir.exists():
            for p in chunks_dir.glob("*.json"):
                try:
                    with open(p, encoding="utf-8") as f:
                        data = json.load(f)
                    chunks = data.get("chunks", [])
                    if chunks:
                        first = chunks[0]
                        meta = first.get("metadata", {})
                        prov = first.get("provenance", {})
                        docs_summary.append(
                            DocumentSummary(
                                document_id=data.get("document_id", p.stem),
                                document_name=meta.get("document_name", p.name),
                                document_type=meta.get("document_type", ".txt"),
                                category=meta.get("category", "general"),
                                academic_year=meta.get("academic_year"),
                                chunk_count=len(chunks),
                                source_file=prov.get("source_file", p.name),
                            )
                        )
                except Exception:
                    continue
        return docs_summary

    def get_health(self) -> HealthResponse:
        """Check system status."""
        manifest = self.vector_store.get_manifest()
        vector_count = manifest.total_vectors if manifest else 0
        bm25_loaded = hasattr(self.bm25_retriever, "index") and len(self.bm25_retriever.index.doc_records) > 0

        # LLM availability check
        llm_avail, llm_msg = self.generator.is_available()

        return HealthResponse(
            status="healthy" if llm_avail else "degraded",
            app_name=self.settings.app_name,
            version="1.0.0",
            llm_provider=self.generator.provider_name,
            llm_model=self.generator.model_name,
            llm_available=llm_avail,
            llm_status_message=llm_msg,
            embedding_provider=self.embedding_model.provider_name,
            vectorstore_records=vector_count,
            bm25_indexed=bm25_loaded,
        )
