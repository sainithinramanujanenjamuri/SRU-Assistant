"""Integration test verifying complete document upload, structure-aware chunking, vector & BM25 indexing, and immediate query resolution."""
from __future__ import annotations

import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.query_service import RAGQueryService

client = TestClient(app)


def test_upload_auto_index_and_retrieval_lifecycle(tmp_path: Path) -> None:
    """Verify that uploading a new academic document with auto_index=True makes it immediately searchable."""
    # Unique academic content
    doc_content = (
        "SR University Special Academic Circular 2026-27\n"
        "Department of Computer Science and Artificial Intelligence\n"
        "Date of Notification: 15 October 2026\n\n"
        "Section 1: Quantum Computing Specialization Course\n"
        "Course Code: 23QNT401T\n"
        "The newly approved prerequisite for Quantum Computing is Advanced Linear Algebra with minimum grade B+.\n"
        "The laboratory requirement requires attendance in 14 hands-on qiskit simulation sessions.\n"
    ).encode("utf-8")

    filename = "sru_quantum_circular_2026.txt"
    files = {"file": (filename, io.BytesIO(doc_content), "text/plain")}

    # 1. Upload with auto_index=True
    response = client.post("/api/documents/upload?auto_index=true", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "indexed"
    assert data["is_duplicate"] is False
    assert "indexed into vector and BM25 stores" in data["message"]

    # 2. Verify document catalog reflects the new document
    catalog_resp = client.get("/api/documents")
    assert catalog_resp.status_code == 200
    catalog = catalog_resp.json()
    assert any("quantum" in d["document_name"].lower() or "sru_quantum_circular_2026" in d["document_name"].lower() for d in catalog)

    # 3. Query the newly indexed passage
    query_payload = {
        "query": "What is the prerequisite for Quantum Computing course 23QNT401T?",
        "top_k": 3,
        "retrieval_mode": "enhanced",
        "verify_citations": True,
    }
    q_resp = client.post("/api/query", json=query_payload)
    assert q_resp.status_code == 200
    q_data = q_resp.json()

    # Verify answer contains facts from newly uploaded document
    assert "Linear Algebra" in q_data["answer"] or "23QNT401T" in q_data["answer"]
    assert len(q_data["citations"]) >= 1
    assert any("quantum" in c["document_name"].lower() for c in q_data["citations"])
    assert q_data["is_grounded"] is True

