"""Automated test suite for SRU Assistant FastAPI application layer (Phase 10)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_api_health_endpoint() -> None:
    """Verify system health endpoint returns 200 and operational telemetry."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["app_name"] == "SRU Assistant"
    assert "llm_provider" in data
    assert "vectorstore_records" in data


def test_api_documents_endpoint() -> None:
    """Verify document catalog endpoint returns indexed institutional documents."""
    response = client.get("/api/documents")
    assert response.status_code == 200
    docs = response.json()
    assert isinstance(docs, list)
    # At least calendar and syllabus should be indexed
    doc_names = [d["document_name"] for d in docs]
    assert any("calendar" in d.lower() for d in doc_names)


def test_api_query_grounded_answer() -> None:
    """Verify POST /api/query returns grounded academic answer and verifiable citations."""
    payload = {
        "query": "When is Mid-Semester Examination I scheduled?",
        "top_k": 5,
        "retrieval_mode": "enhanced",
        "verify_citations": True,
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "Mid-Semester Examination I" in data["answer"]
    assert "12 September 2026" in data["answer"]
    assert len(data["citations"]) >= 1
    assert data["is_grounded"] is True
    assert data["verification"]["citation_precision"] == 1.0
    assert data["verification"]["overall_support_score"] >= 0.7



def test_api_query_safe_refusal() -> None:
    """Verify out-of-domain queries trigger safe zero-hallucination fallback."""
    payload = {
        "query": "What are the rules regarding campus parking permits and automobile registration fees?",
        "top_k": 5,
        "retrieval_mode": "enhanced",
        "verify_citations": True,
    }
    response = client.post("/api/query", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "sufficient information" in data["answer"].lower() or "insufficient" in data["answer"].lower()
    assert data["verification"]["unsupported_claims_count"] == 0


def test_api_query_validation_error() -> None:
    """Verify empty query triggers 422 Unprocessable Entity."""
    payload = {"query": ""}
    response = client.post("/api/query", json=payload)
    assert response.status_code == 422


def test_api_static_frontend_routes() -> None:
    """Verify root and presentation routes serve frontend HTML pages."""
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert "text/html" in resp_root.headers.get("content-type", "")

    resp_pres = client.get("/presentation")
    assert resp_pres.status_code == 200
    assert "text/html" in resp_pres.headers.get("content-type", "")

    resp_docs = client.get("/docs")
    assert resp_docs.status_code == 200
