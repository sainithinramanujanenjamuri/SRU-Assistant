"""API endpoints for SRU Assistant (Phase 10 & Phase 11)."""

from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile, status

from app.api.schemas import (
    DocumentSummary,
    DocumentUploadResponse,
    HealthResponse,
    QueryRequest,
    QueryResponse,
)
from app.security import DocumentSecurityError, QuerySecurityError
from app.services.query_service import RAGQueryService

router = APIRouter(prefix="/api", tags=["Academic RAG"])


@router.post("/query", response_model=QueryResponse, summary="Query SR University Academic Knowledge Base")
def answer_academic_query(req: QueryRequest) -> QueryResponse:
    """Execute end-to-end grounded query resolution.
    
    Returns synthesized answer strictly grounded in university evidence,
    accompanied by verified citations, page provenance, and execution telemetry.
    """
    try:
        service = RAGQueryService.get_instance()
        return service.query(req)
    except QuerySecurityError as qse:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(qse),
        ) from qse
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error executing academic query resolution: {e}",
        ) from e


@router.post("/documents/upload", response_model=DocumentUploadResponse, summary="Securely Upload Academic Document")
async def upload_academic_document(
    file: UploadFile = File(...),
    auto_index: bool = False,
) -> DocumentUploadResponse:
    """Upload an official academic document (.pdf, .docx, .txt) with Phase 11 security validation.
    
    If auto_index is True, triggers immediate document processing, chunking, and dual-index registration.
    """
    service = RAGQueryService.get_instance()
    filename = file.filename or "unknown.txt"
    try:
        # Bounded streaming read preventing memory exhaustion / DoS
        max_bytes = service.document_guard.max_size_bytes
        chunk_size = 64 * 1024  # 64 KB
        chunks: list[bytes] = []
        total_bytes = 0

        while True:
            chunk = await file.read(chunk_size)
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                raise DocumentSecurityError(
                    f"File '{filename}' exceeds maximum permitted size of {max_bytes} bytes ({max_bytes / (1024 * 1024):.1f} MB)."
                )
            chunks.append(chunk)

        content = b"".join(chunks)
        res = service.validate_and_save_document(filename, content)
        if res.is_duplicate:
            return DocumentUploadResponse(
                filename=res.safe_filename,
                status="duplicate",
                file_size_bytes=res.file_size_bytes,
                sha256_hash=res.sha256_hash,
                is_duplicate=True,
                message=f"Document '{res.safe_filename}' already exists with identical SHA-256 hash.",
            )

        status_msg = f"Document '{res.safe_filename}' validated and stored for ingestion."
        if auto_index:
            from pathlib import Path
            raw_path = Path(service.settings.raw_documents_dir) / res.safe_filename
            try:
                idx_report = service.ingest_and_index_file(raw_path)
                status_msg = (
                    f"Document '{res.safe_filename}' successfully processed, chunked ({idx_report['chunks_count']} chunks), "
                    f"and indexed into vector and BM25 stores."
                )
                return DocumentUploadResponse(
                    filename=res.safe_filename,
                    status="indexed",
                    file_size_bytes=res.file_size_bytes,
                    sha256_hash=res.sha256_hash,
                    is_duplicate=False,
                    message=status_msg,
                )
            except Exception as e:
                # Cleanup raw file on indexing failure to prevent inconsistent unindexed raw files
                if raw_path.exists():
                    try:
                        raw_path.unlink()
                    except Exception:
                        pass
                raise e

        return DocumentUploadResponse(
            filename=res.safe_filename,
            status="uploaded",
            file_size_bytes=res.file_size_bytes,
            sha256_hash=res.sha256_hash,
            is_duplicate=False,
            message=status_msg,
        )
    except DocumentSecurityError as dse:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(dse),
        ) from dse
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process document upload: {e}",
        ) from e


@router.get("/documents", response_model=list[DocumentSummary], summary="List Indexed Academic Documents")
def list_academic_documents() -> list[DocumentSummary]:
    """Retrieve catalog of indexed institutional documents and chunk counts."""
    service = RAGQueryService.get_instance()
    return service.get_documents()


@router.get("/health", response_model=HealthResponse, summary="System Health & Provider Status")
def healthcheck() -> HealthResponse:
    """Inspect system operational status, active LLM provider, and vector store indices."""
    service = RAGQueryService.get_instance()
    return service.get_health()

