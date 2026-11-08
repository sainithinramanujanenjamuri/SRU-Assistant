# SRU Assistant — Project Memory

## Purpose of Project Memory

`project_memory/` is the persistent historical development record of the **SRU Assistant** project. It documents engineering decisions, phase completions, validation evidence, failed attempts, and architecture evolution over time.

### What Project Memory Is NOT:

- It is **NOT** RAG memory (e.g., retrieved context or chunk caches).
- It is **NOT** Vector database memory or index storage.
- It is **NOT** LLM conversation buffer or context memory.
- It is **NOT** User session memory or user profile storage.
- It is **NOT** Runtime system memory.

It is strictly an engineering record and audit trail of actual project progress and empirical verification.

---

## Current Project State

- **Current Phase:** Phase 14 — Deployment & Demonstration
- **Current Objective:** Deliver Viva Presentation slide deck, final thesis report, and end-to-end evaluation showcase for Capstone Team 235.
- **Last Completed Phase:** Phase 13 — Final Integration
- **Next Phase:** Final Viva Evaluation & Department Showcase
- **Current Architecture Version:** Phase 14 Production-Ready RAG Framework (FastAPI REST Backend + Query Guard + Document Guard + Hybrid RRF Retriever + Grounded Generator + Citation Verifier + Responsive Glassmorphic Web UI + Interactive Presentation Deck)
- **Current RAG Version:** Full Grounded & Hardened RAG System (Enhanced Hybrid Retriever + RRF + Re-ranker + Grounded Generator + Citation Verifier + Query Guard + Document Guard + Acronym Expander)
- **Known Blockers:** None

---

## Roadmap Phase Status Tracking

| Phase | Phase Name | Status | Report |
|---|---|---|---|
| 00 | Project Foundation | COMPLETED | [phase_00_project_foundation.md](phase_00_project_foundation.md) |
| 01 | Document Intelligence | COMPLETED | [phase_01_document_intelligence.md](phase_01_document_intelligence.md) |
| 02 | Knowledge Preparation | COMPLETED | [phase_02_knowledge_preparation.md](phase_02_knowledge_preparation.md) |
| 03 | Embedding & Vector Store | COMPLETED | [phase_03_embedding_vector_store.md](phase_03_embedding_vector_store.md) |
| 04 | Baseline RAG | COMPLETED | [phase_04_baseline_rag.md](phase_04_baseline_rag.md) |
| 05 | Hybrid Retrieval | COMPLETED | [phase_05_hybrid_retrieval.md](phase_05_hybrid_retrieval.md) |
| 06 | Retrieval Enhancement | COMPLETED | [phase_06_retrieval_enhancement.md](phase_06_retrieval_enhancement.md) |
| 07 | Grounded Generation | COMPLETED | [phase_07_grounded_generation.md](phase_07_grounded_generation.md) |
| 08 | Citation & Provenance | COMPLETED | [phase_08_citation_provenance.md](phase_08_citation_provenance.md) |
| 09 | RAG Evaluation | COMPLETED | [phase_09_rag_evaluation.md](phase_09_rag_evaluation.md) |
| 10 | Application Layer | COMPLETED | [phase_10_application_layer.md](phase_10_application_layer.md) |
| 11 | Reliability & Security | COMPLETED | [phase_11_reliability_security.md](phase_11_reliability_security.md) |
| 12 | Advanced RAG Research | COMPLETED | [phase_12_advanced_rag_research.md](phase_12_advanced_rag_research.md) |
| 13 | Final Integration | COMPLETED | [phase_13_final_integration.md](phase_13_final_integration.md) |
| 14 | Deployment & Demonstration | COMPLETED | [phase_14_deployment_demonstration.md](phase_14_deployment_demonstration.md) |

---

## Guidelines for Updating Project Memory

1. **Evidence Rules:** Never record "Tests passed" without recording the exact command executed and the actual output.
2. **Phase Completion Rule:** A phase is marked `COMPLETED` only after implementation, tests, validation, and documentation are verified.
3. **Preserve History:** Do not delete failed experiments or architectural transitions. Document them to ensure clear engineering rationale.
