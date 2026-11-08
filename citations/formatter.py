"""Citation rendering and formatting subsystem supporting inline brackets, source blocks, and footnotes."""
from __future__ import annotations


import re
from typing import Literal

from citations.models import CitationItem, ClaimItem

CitationStyle = Literal["inline_bracket", "source_block", "footnote"]


class CitationFormatter:
    """Renders grounded answers with academic citations according to institutional formatting styles.


    Supported styles:
    - 'inline_bracket': Appends numeric brackets '[1]' to claims and lists bibliographical sources at bottom.
    - 'source_block': Preserves clean answer body and appends structured provenance source block.
    - 'footnote': Appends superscript numeral markers ('¹', '²') and lists footnotes at bottom.
    """

    SUPERSCRIPTS = {
        "0": "⁰",
        "1": "¹",
        "2": "²",
        "3": "³",
        "4": "⁴",
        "5": "⁵",
        "6": "⁶",
        "7": "⁷",
        "8": "⁸",
        "9": "⁹",
    }

    def format(
        self,
        answer: str,
        citations: list[CitationItem],
        claims: list[ClaimItem] | None = None,
        style: CitationStyle = "inline_bracket",
    ) -> str:
        """Format answer and citations using the specified style."""
        if not citations or not answer.strip():
            return answer

        if style == "inline_bracket":
            return self.format_inline_bracket(answer, citations, claims or [])
        elif style == "source_block":
            return self.format_source_block(answer, citations)
        elif style == "footnote":
            return self.format_footnote(answer, citations, claims or [])
        else:
            raise ValueError(
                f"Unsupported citation style '{style}'. Must be one of: 'inline_bracket', 'source_block', 'footnote'"
            )

    def format_inline_bracket(
        self,
        answer: str,
        citations: list[CitationItem],
        claims: list[ClaimItem],
    ) -> str:
        """Render answer with inline bracket indicators (e.g. '[1]', '[1, 2]') and source list."""
        annotated_body = answer
        citations_by_id = {c.citation_id: c for c in citations}

        # Embed inline citation indicators on matching claims
        for claim in claims:
            if not claim.associated_citation_ids:
                continue

            valid_cit_ids = [
                cid for cid in claim.associated_citation_ids if cid in citations_by_id
            ]
            if not valid_cit_ids:
                continue

            marker = f" [{', '.join(valid_cit_ids)}]"

            # Find claim location in answer body
            annotated_body = self._insert_marker(annotated_body, claim.claim_text, marker)

        # Append formatted bibliography
        sources_list = ["\n\nSources:"]
        for cit in citations:
            line = f"[{cit.citation_id}] {cit.source}"
            if cit.section and cit.section != "N/A" and f"Section: {cit.section}" not in cit.source:
                line += f"\n    Section: {cit.section}"
            sources_list.append(line)

        return annotated_body.strip() + "\n" + "\n".join(sources_list)

    def format_source_block(
        self,
        answer: str,
        citations: list[CitationItem],
    ) -> str:
        """Render clean answer followed by a structured source attribution block."""
        clean_body = answer.strip()
        source_header = "Source:" if len(citations) == 1 else "Sources:"
        sources_list = [f"\n\n{source_header}"]

        for cit in citations:
            line = f"- {cit.source}"
            if cit.section and cit.section != "N/A" and f"Section: {cit.section}" not in cit.source:
                line += f"\n  Section: {cit.section}"
            sources_list.append(line)

        return clean_body + "\n" + "\n".join(sources_list)

    def format_footnote(
        self,
        answer: str,
        citations: list[CitationItem],
        claims: list[ClaimItem],
    ) -> str:
        """Render answer with superscript footnote markers (e.g. '¹', '²') and footnotes list."""
        annotated_body = answer
        citations_by_id = {c.citation_id: c for c in citations}

        for claim in claims:
            if not claim.associated_citation_ids:
                continue

            valid_cit_ids = [
                cid for cid in claim.associated_citation_ids if cid in citations_by_id
            ]
            if not valid_cit_ids:
                continue

            superscript_str = "".join(
                "".join(self.SUPERSCRIPTS.get(ch, ch) for ch in cid)
                for cid in valid_cit_ids
            )

            annotated_body = self._insert_marker(annotated_body, claim.claim_text, superscript_str)

        # Append Footnotes section
        footnotes_list = ["\n\nFootnotes:"]
        for cit in citations:
            sup_id = "".join(self.SUPERSCRIPTS.get(ch, ch) for ch in cit.citation_id)
            line = f"{sup_id} {cit.source}"
            if cit.section and cit.section != "N/A" and f"Section: {cit.section}" not in cit.source:
                line += f" (Section: {cit.section})"
            footnotes_list.append(line)

        return annotated_body.strip() + "\n" + "\n".join(footnotes_list)

    def _insert_marker(self, body: str, claim_text: str, marker: str) -> str:
        """Insert a citation marker at the end of the sentence or clause corresponding to claim_text."""
        # Check for exact substring match
        clean_claim = claim_text.rstrip(".!? ")
        pattern = re.compile(re.escape(clean_claim) + r"([.!?]?)", re.IGNORECASE)

        def replace_with_marker(m: re.Match) -> str:
            punctuation = m.group(1) or ""
            return f"{m.group(0)}{marker}" if punctuation else f"{m.group(0)}{marker}"

        if pattern.search(body):
            # Replace only the first occurrence to avoid duplicates
            return pattern.sub(replace_with_marker, body, count=1)

        return body
