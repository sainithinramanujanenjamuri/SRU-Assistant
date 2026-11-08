"""Integration tests verifying live local Ollama neural LLM generation, strict evidence grounding, citation integrity, and diagnostics."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api.schemas import QueryRequest
from app.main import app
from app.services.query_service import RAGQueryService
from generation.llm.ollama import OllamaLLMClient
from generation.models import LLMProviderUnavailableError
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK

client = TestClient(app)


@pytest.fixture(scope="module")
def ensure_ollama_available():
    """Verify local Ollama daemon is reachable; skip test if offline."""
    probe = OllamaLLMClient(model_name="qwen2.5:0.5b", base_url="http://localhost:11434")
    available, msg = probe.is_available()
    if not available and "Cannot connect" in msg:
        pytest.skip(f"Local Ollama service offline: {msg}")
    return probe


class TestOllamaDiagnostics:
    """Diagnostic tests for Ollama daemon and model availability."""

    def test_unreachable_endpoint_actionable_error(self):
        offline_client = OllamaLLMClient(base_url="http://localhost:59999")
        available, msg = offline_client.is_available()
        assert available is False
        assert "Cannot connect" in msg
        assert "ollama serve" in msg

    def test_unreachable_generate_raises_actionable_exception(self):
        offline_client = OllamaLLMClient(base_url="http://localhost:59999", timeout_seconds=1.0)
        with pytest.raises(LLMProviderUnavailableError) as exc_info:
            offline_client.generate(prompt="Test question")
        assert "Cannot connect" in str(exc_info.value)
        assert "ollama serve" in str(exc_info.value)

    def test_missing_model_actionable_message(self, ensure_ollama_available):
        missing_client = OllamaLLMClient(model_name="nonexistent_test_model:99b", base_url="http://localhost:11434")
        available, msg = missing_client.is_available()
        assert available is False
        assert "not pulled" in msg
        assert "ollama pull nonexistent_test_model:99b" in msg


class TestLiveOllamaGenerationAndGrounding:
    """Verify live generation, grounded evidence synthesis, and citation provenance."""

    @pytest.mark.parametrize("model_name", ["qwen2.5:0.5b", "llama3.2:1b"])
    def test_live_generation_multi_model(self, ensure_ollama_available, model_name: str):
        """Verify lightweight neural models actively generate text with valid token counts and latency."""
        llm = OllamaLLMClient(model_name=model_name, temperature=0.0, max_tokens=128)
        avail, _ = llm.is_available()
        if not avail:
            pytest.skip(f"Model {model_name} not installed locally.")

        resp = llm.generate("State the role of an academic calendar in one sentence.")
        assert resp.is_llm is True
        assert resp.provider_name == "ollama"
        assert resp.model_name == model_name
        assert len(resp.text.strip()) > 10
        assert resp.latency_ms > 0.0

    def test_grounded_answer_with_citation_provenance(self, ensure_ollama_available):
        """Verify live LLM answers academic query with evidence grounding and citation matching."""
        service = RAGQueryService.get_instance()
        orig_generator = service.generator
        try:
            service.generator = OllamaLLMClient(model_name="qwen2.5:0.5b", temperature=0.0)
            req = QueryRequest(
                query="When is Mid-Semester Examination I scheduled?",
                top_k=5,
                retrieval_mode="enhanced",
                verify_citations=True,
            )
            res = service.query(req)

            assert res.is_grounded is True
            assert len(res.answer.strip()) > 0
            assert len(res.citations) >= 1

            # Citations must carry accurate provenance
            first_cit = res.citations[0]
            assert any(doc in first_cit.document_name.lower() for doc in ["calendar", "regulations", "syllabus"])
            assert first_cit.chunk_id is not None
            assert "[" in res.cited_answer and "]" in res.cited_answer

            # Verification metrics
            assert res.verification.citation_precision == 1.0
            assert res.verification.unsupported_claims_count == 0
        finally:
            service.generator = orig_generator

    def test_grounded_answer_with_llama32(self, ensure_ollama_available):
        """Verify Llama 3.2 1B generates grounded academic answers with verified citations."""
        service = RAGQueryService.get_instance()
        orig_generator = service.generator
        try:
            service.generator = OllamaLLMClient(model_name="llama3.2:1b", temperature=0.0)
            avail, _ = service.generator.is_available()
            if not avail:
                pytest.skip("llama3.2:1b not installed locally")
            req = QueryRequest(
                query="When is Mid-Semester Examination I scheduled?",
                top_k=5,
                retrieval_mode="enhanced",
                verify_citations=True,
            )
            res = service.query(req)
            assert res.is_grounded is True
            assert len(res.answer.strip()) > 0
            assert len(res.citations) >= 1
            assert any(doc in res.citations[0].document_name.lower() for doc in ["calendar", "regulations"])
        finally:
            service.generator = orig_generator

    def test_out_of_domain_safe_refusal(self, ensure_ollama_available):
        """Verify safe refusal without hallucination for queries outside institutional scope."""
        service = RAGQueryService.get_instance()
        orig_generator = service.generator
        try:
            service.generator = OllamaLLMClient(model_name="qwen2.5:0.5b", temperature=0.0)
            req = QueryRequest(
                query="What are the rules regarding campus parking permits and automobile registration fees?",
                top_k=5,
                retrieval_mode="enhanced",
                verify_citations=True,
            )
            res = service.query(req)

            # Pipeline must trigger safe refusal
            assert INSUFFICIENT_EVIDENCE_FALLBACK in res.answer or "insufficient" in res.answer.lower()
            assert res.is_grounded is True
            assert len(res.citations) == 0
            assert res.verification.unsupported_claims_count == 0
        finally:
            service.generator = orig_generator

    def test_qwen35_live_generation_non_empty(self, ensure_ollama_available):
        """Verify Qwen3.5:4b generates clean, non-empty text without raw thinking tags."""
        llm = OllamaLLMClient(
            model_name="qwen3.5:4b",
            temperature=0.0,
            max_tokens=256,
            enable_thinking=False,
            endpoint="chat",
        )
        avail, _ = llm.is_available()
        if not avail:
            pytest.skip("Model qwen3.5:4b not installed locally.")

        resp = llm.generate("State the role of an academic calendar in one sentence.")
        assert resp.is_llm is True
        assert resp.provider_name == "ollama"
        assert resp.model_name == "qwen3.5:4b"
        assert len(resp.text.strip()) > 10
        assert "<think>" not in resp.text
        assert "</think>" not in resp.text
        assert resp.latency_ms > 0.0

    def test_qwen35_grounded_answer_with_citations(self, ensure_ollama_available):
        """Verify Qwen3.5:4b resolves academic query with evidence grounding and verified citations."""
        service = RAGQueryService.get_instance()
        orig_generator = service.generator
        try:
            service.generator = OllamaLLMClient(
                model_name="qwen3.5:4b",
                temperature=0.0,
                enable_thinking=False,
                endpoint="chat",
            )
            avail, _ = service.generator.is_available()
            if not avail:
                pytest.skip("Model qwen3.5:4b not installed locally.")

            req = QueryRequest(
                query="When is Mid-Semester Examination I scheduled?",
                top_k=5,
                retrieval_mode="enhanced",
                verify_citations=True,
            )
            res = service.query(req)
            assert res.is_grounded is True
            assert len(res.answer.strip()) > 0
            assert len(res.citations) >= 1
            assert "[" in res.cited_answer and "]" in res.cited_answer
            assert res.verification.citation_precision >= 0.8
        finally:
            service.generator = orig_generator


class TestLiveOllamaAPIEndpoints:
    """Verify FastAPI /api/health and /api/query endpoints with live Ollama provider."""

    def test_health_endpoint_diagnostics_healthy(self, ensure_ollama_available):
        service = RAGQueryService.get_instance()
        orig_generator = service.generator
        try:
            service.generator = OllamaLLMClient(model_name="qwen3.5:4b")
            resp = client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "healthy"
            assert data["llm_provider"] == "ollama"
            assert data["llm_model"] == "qwen3.5:4b"
            assert data["llm_available"] is True
            assert data["llm_status_message"] == "Available"
        finally:
            service.generator = orig_generator

    def test_health_endpoint_diagnostics_degraded(self):
        service = RAGQueryService.get_instance()
        orig_generator = service.generator
        try:
            service.generator = OllamaLLMClient(model_name="offline-model", base_url="http://localhost:59999")
            resp = client.get("/api/health")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "degraded"
            assert data["llm_provider"] == "ollama"
            assert data["llm_available"] is False
            assert "Cannot connect" in data["llm_status_message"]
        finally:
            service.generator = orig_generator

    def test_api_query_with_live_ollama(self, ensure_ollama_available):
        service = RAGQueryService.get_instance()
        orig_generator = service.generator
        try:
            service.generator = OllamaLLMClient(model_name="qwen2.5:0.5b", temperature=0.0)
            payload = {
                "query": "When is Mid-Semester Examination I scheduled?",
                "top_k": 5,
                "retrieval_mode": "enhanced",
                "verify_citations": True,
            }
            resp = client.post("/api/query", json=payload)
            assert resp.status_code == 200
            data = resp.json()
            assert data["is_grounded"] is True
            assert len(data["citations"]) >= 1
            assert data["engine_info"]["provider"] == "ollama"
            assert data["engine_info"]["model"] == "qwen2.5:0.5b"
            assert data["engine_info"]["is_llm"] is True
        finally:
            service.generator = orig_generator
