"""Unit tests for GroundedPromptTemplate and grounding instructions."""

from generation.models import RAGPromptContext, RetrievedEvidence
from generation.prompts.templates import (
    INSUFFICIENT_EVIDENCE_FALLBACK,
    GroundedPromptTemplate,
)


class TestGroundedPromptTemplate:
    """Test prompt rendering and grounding constraints."""

    def test_system_prompt_grounding_directives(self):
        template = GroundedPromptTemplate()
        sys_prompt = template.render_system_prompt()

        assert "SR University" in sys_prompt
        assert "EVIDENCE section" in sys_prompt
        assert "Do NOT fabricate" in sys_prompt
        assert INSUFFICIENT_EVIDENCE_FALLBACK in sys_prompt
        assert "Security & Prompt Injection Defense" in sys_prompt

    def test_user_prompt_structure_and_separation(self):
        template = GroundedPromptTemplate()
        ctx = RAGPromptContext(
            query="When are mid examinations?",
            evidence_items=[
                RetrievedEvidence(
                    chunk_id="c1",
                    document_id="doc1",
                    document_name="calendar.txt",
                    section_path="Examinations",
                    page_info="p. 1",
                    text="Mid exams start September 12.",
                    score=0.85,
                    cosine_similarity=0.70,
                )
            ],
            formatted_context_text="<evidence id='1'>Mid exams start September 12.</evidence>",
            total_evidence_tokens=10,
            has_sufficient_evidence=True,
        )

        user_prompt = template.render_user_prompt(ctx)
        assert "### RETRIEVED UNIVERSITY EVIDENCE" in user_prompt
        assert "### STUDENT ACADEMIC QUESTION:" in user_prompt
        assert "### GROUNDED ANSWER:" in user_prompt
        assert "<evidence id='1'>Mid exams start September 12.</evidence>" in user_prompt
        assert "When are mid examinations?" in user_prompt

    def test_empty_evidence_prompt_rendering(self):
        template = GroundedPromptTemplate()
        ctx = RAGPromptContext(
            query="sports quota rules",
            evidence_items=[],
            formatted_context_text="",
            total_evidence_tokens=0,
            has_sufficient_evidence=False,
        )

        user_prompt = template.render_user_prompt(ctx)
        assert "[No relevant institutional documents retrieved]" in user_prompt
        assert "sports quota rules" in user_prompt
