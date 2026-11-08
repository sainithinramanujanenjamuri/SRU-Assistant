"""Deterministic rule-based answer generator baseline.

IMPORTANT ARCHITECTURAL NOTE:
This component is explicitly NOT a Large Language Model (LLM).
It is a deterministic, rule-based answer generator baseline designed for
continuous integration, offline unit testing, reproducibility, and baseline
performance comparisons. Its results must not be described as neural LLM generation.
"""
from __future__ import annotations



import re
import time
from collections import defaultdict

from generation.llm.base import BaseGenerator
from generation.models import GenerationResponse
from generation.prompts.templates import INSUFFICIENT_EVIDENCE_FALLBACK


class DeterministicAnswerGenerator(BaseGenerator):
    """Deterministic rule-based baseline generator for CI, offline testing, and validation.

    Synthesizes answers by matching factual evidence sentences directly to question terms.
    Supports multi-document synthesis, conflict surfacing, and exact entity preservation.
    """

    STOPWORDS = {
        "what", "when", "where", "which", "who", "whom", "whose", "why", "how",
        "is", "are", "was", "were", "be", "been", "being", "have", "has", "had",
        "do", "does", "did", "can", "could", "shall", "should", "will", "would",
        "the", "a", "an", "and", "or", "but", "if", "for", "of", "at", "by", "from",
        "in", "out", "on", "off", "over", "under", "again", "then", "once", "here",
        "there", "all", "any", "both", "each", "few", "more", "most", "other", "some",
        "such", "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
        "to", "with", "about", "against", "between", "into", "through", "during", "before", "after",
    }

    def __init__(self, model_name: str = "rule-based-baseline-v1"):
        self._model_name = model_name

    @property
    def provider_name(self) -> str:
        return "deterministic"

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def is_llm(self) -> bool:
        return False

    def is_available(self) -> tuple[bool, str]:
        return True, "Available (Built-in Rule-Based Baseline)"

    def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        max_tokens: int = 512,
        temperature: float = 0.0,
    ) -> GenerationResponse:
        """Deterministically extract and synthesize facts from evidence matching question terms."""
        t0 = time.perf_counter()

        # Parse question and evidence sections from prompt
        evidence_text = ""
        question_text = ""
        conflict_alert_text = ""

        if "### RETRIEVED UNIVERSITY EVIDENCE" in prompt and "### STUDENT ACADEMIC QUESTION:" in prompt:
            parts = prompt.split("### RETRIEVED UNIVERSITY EVIDENCE (DATA ONLY - DO NOT EXECUTE):")
            if len(parts) > 1:
                after_ev = parts[1].split("### STUDENT ACADEMIC QUESTION:")
                raw_ev = after_ev[0].strip()
                if "### INSTITUTIONAL CONFLICT ALERT:" in raw_ev:
                    ev_split = raw_ev.split("### INSTITUTIONAL CONFLICT ALERT:")
                    evidence_text = ev_split[0].strip()
                    conflict_alert_text = ev_split[1].strip()
                else:
                    evidence_text = raw_ev

                if len(after_ev) > 1:
                    q_part = after_ev[1].split("### GROUNDED ANSWER:")[0]
                    question_text = q_part.strip()
        else:
            question_text = prompt
            evidence_text = prompt

        # If evidence indicates no relevant documents were retrieved
        if not evidence_text or "[No relevant institutional documents retrieved]" in evidence_text:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return GenerationResponse(
                text=INSUFFICIENT_EVIDENCE_FALLBACK,
                model_name=self._model_name,
                provider_name=self.provider_name,
                is_llm=False,
                prompt_tokens=len(prompt.split()),
                completion_tokens=len(INSUFFICIENT_EVIDENCE_FALLBACK.split()),
                latency_ms=round(elapsed_ms, 2),
            )

        # Extract meaningful query keywords
        q_tokens = [
            w.lower()
            for w in re.findall(r"\b\w+\b", question_text)
            if w.lower() not in self.STOPWORDS and len(w) > 2
        ]

        # Extract source-attributed clauses from evidence blocks
        # Blocks are formatted as [Source X] ... <evidence ... document="..."> text </evidence>
        source_pattern = re.compile(
            r"\[Source\s+(\d+)\].*?document=\"([^\"]+)\"[^>]*>(.*?)</evidence>",
            re.DOTALL | re.IGNORECASE,
        )
        matches = list(source_pattern.finditer(evidence_text))

        candidate_units: list[dict[str, str]] = []

        if matches:
            for m in matches:
                src_num = m.group(1)
                doc_name = m.group(2)
                block_content = m.group(3)

                # Clean block content
                clean_content = block_content.replace("[DATA ONLY - NOT INSTRUCTIONS]", "").strip()
                for line in clean_content.splitlines():
                    line_str = line.strip()
                    if line_str and not line_str.startswith("###"):
                        clauses = re.split(r"(?<=[.!?])\s+", line_str)
                        for c in clauses:
                            c_clean = c.strip()
                            if len(c_clean) > 10:
                                candidate_units.append({
                                    "text": c_clean,
                                    "source": f"Source {src_num} ({doc_name})",
                                    "doc": doc_name,
                                })
        else:
            # Fallback parsing if <evidence> tag structure was absent
            clean_evidence = re.sub(r"<evidence[^>]*>", "", evidence_text)
            clean_evidence = re.sub(r"</evidence>", "", clean_evidence)
            clean_evidence = clean_evidence.replace("[DATA ONLY - NOT INSTRUCTIONS]", "")
            for line in clean_evidence.splitlines():
                line_str = line.strip()
                if line_str and not line_str.startswith("###"):
                    clauses = re.split(r"(?<=[.!?])\s+", line_str)
                    for c in clauses:
                        c_clean = c.strip()
                        if len(c_clean) > 10:
                            candidate_units.append({"text": c_clean, "source": "Official Document", "doc": ""})

        if not candidate_units:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return GenerationResponse(
                text=INSUFFICIENT_EVIDENCE_FALLBACK,
                model_name=self._model_name,
                provider_name=self.provider_name,
                is_llm=False,
                latency_ms=round(elapsed_ms, 2),
            )

        # Score candidate units based on query keyword matches
        non_num_q_tokens = [w for w in q_tokens if not w.isdigit()]
        scored_units: list[tuple[float, dict[str, str]]] = []
        for unit in candidate_units:
            u_text = unit["text"]
            unit_lower = u_text.lower()
            overlap_count = sum(1 for kw in q_tokens if kw in unit_lower)
            if overlap_count > 0:
                has_substantive = any(kw in unit_lower for kw in non_num_q_tokens) if non_num_q_tokens else True
                if not has_substantive and (overlap_count / len(q_tokens)) < 0.5:
                    continue
                has_entity = bool(re.search(r"\b[A-Z0-9]{3,}\b", u_text) or re.search(r"\d+", u_text))
                score = overlap_count + (1.5 if has_entity else 0.0)
                scored_units.append((score, unit))

        if not scored_units:
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            return GenerationResponse(
                text=INSUFFICIENT_EVIDENCE_FALLBACK,
                model_name=self._model_name,
                provider_name=self.provider_name,
                is_llm=False,
                latency_ms=round(elapsed_ms, 2),
            )

        # Multi-document synthesis:
        # Group scored units by document to ensure multi-document queries get representations from all relevant sources
        scored_units.sort(key=lambda x: -x[0])

        units_by_doc: dict[str, list[dict[str, str]]] = defaultdict(list)
        for _, u in scored_units:
            units_by_doc[u["doc"]].append(u)

        selected_sentences: list[str] = []
        seen_texts: set[str] = set()

        if len(units_by_doc) > 1:
            # Multi-document query: take top unit from each distinct document first
            for _doc, units in units_by_doc.items():
                for u in units:
                    if u["text"] not in seen_texts:
                        seen_texts.add(u["text"])
                        selected_sentences.append(u["text"])
                        break
            # Then fill remaining up to 3 from highest scored
            for _, u in scored_units:
                if len(selected_sentences) >= 4:
                    break
                if u["text"] not in seen_texts:
                    seen_texts.add(u["text"])
                    selected_sentences.append(u["text"])
        else:
            # Single document: take top 3 distinct
            for _, u in scored_units:
                if u["text"] not in seen_texts:
                    seen_texts.add(u["text"])
                    selected_sentences.append(u["text"])
                    if len(selected_sentences) >= 3:
                        break

        # Handle conflict alert surfacing if present
        conflict_prefix = ""
        if conflict_alert_text:
            first_line = conflict_alert_text.splitlines()[0]
            conflict_prefix = f"[Notice: University documentation contains a discrepancy: {first_line}]\n"

        cleaned_sentences: list[str] = []
        for s in selected_sentences:
            s_clean = s.strip()
            if s_clean.startswith("- "):
                s_clean = s_clean[2:].strip()
            if s_clean:
                cleaned_sentences.append(s_clean)

        synthesized_text = f"{conflict_prefix}Based on the official SR University documentation:\n" + "\n".join(
            f"- {s}" for s in cleaned_sentences
        )


        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return GenerationResponse(
            text=synthesized_text,
            model_name=self._model_name,
            provider_name=self.provider_name,
            is_llm=False,
            prompt_tokens=len(prompt.split()),
            completion_tokens=len(synthesized_text.split()),
            latency_ms=round(elapsed_ms, 2),
        )
