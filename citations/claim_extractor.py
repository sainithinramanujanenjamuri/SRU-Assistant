"""Claim extraction and proposition decomposition for university academic answers."""

import re
from typing import ClassVar

from citations.models import ClaimItem, ClaimType
from generation.grounding.entities import AcademicEntityExtractor


class ClaimExtractor:
    """Extracts discrete, verifiable factual propositions from synthesized academic answers.

    Guarantees:
    - Preserves institutional and personal honorific abbreviations (Dr., Prof., p., No., B.Tech., M.Tech., etc.).
    - Strips meta/conversational rhetorical framing ('Based on the documents...', 'Here is the information...').
    - Classifies claims into domain types: 'date', 'policy', 'factual', or 'general'.
    - Identifies academic entities per claim using AcademicEntityExtractor.
    - Generates stable, deterministic sequential claim identifiers ('claim_1', 'claim_2', ...).
    """

    # Protected abbreviations that must not trigger a sentence split
    PROTECTED_ABBREVIATIONS: ClassVar[list[str]] = [
        "dr",
        "prof",
        "mr",
        "mrs",
        "ms",
        "p",
        "pp",
        "no",
        "nos",
        "vol",
        "sec",
        "ref",
        "b.tech",
        "m.tech",
        "ph.d",
        "m.sc",
        "b.sc",
        "m.b.a",
        "b.a",
        "dept",
        "univ",
        "e.g",
        "i.e",
        "etc",
        "vs",
        "sr",
        "jr",
    ]

    # Conversational / rhetorical phrases to remove or ignore entirely
    META_PREFIX_PATTERNS: ClassVar[list[re.Pattern]] = [
        re.compile(
            r"^based on (?:the\s+)?(?:official|provided|available|retrieved)?\s*(?:university\s+)?(?:documents|records|evidence|context|sources|calendar)[,\s:]*",
            re.IGNORECASE,
        ),
        re.compile(
            r"^according to (?:the\s+)?(?:official|provided|available|retrieved)?\s*(?:university\s+)?(?:documents|records|evidence|context|sources|regulations|calendar)[,\s:]*",
            re.IGNORECASE,
        ),
        re.compile(r"^here is the (?:information|answer|details)[,\s:]*", re.IGNORECASE),
        re.compile(
            r"^as per (?:the\s+)?(?:official|available|retrieved)?\s*(?:university\s+)?(?:documents|records|regulations|academic calendar)[,\s:]*",
            re.IGNORECASE,
        ),
        re.compile(r"^in summary[,\s:]*", re.IGNORECASE),
        re.compile(r"^to summarize[,\s:]*", re.IGNORECASE),
        re.compile(r"^please note that[,\s:]*", re.IGNORECASE),
    ]

    DISCARD_SENTENCE_PATTERNS: ClassVar[list[re.Pattern]] = [
        re.compile(r"^based on (?:the )?(?:official )?(?:sr university )?(?:documentation|documents|records|sources|evidence)[,:\s]*$", re.IGNORECASE),
        re.compile(r"^according to (?:the )?(?:official )?(?:sr university )?(?:documentation|documents|records|sources|evidence)[,:\s]*$", re.IGNORECASE),
        re.compile(r"^i couldn't find sufficient information", re.IGNORECASE),
        re.compile(r"^i hope this (?:information )?helps", re.IGNORECASE),
        re.compile(r"^please let me know if you (?:have|need)", re.IGNORECASE),
        re.compile(r"^feel free to ask", re.IGNORECASE),
        re.compile(r"^for more details,?\s*(?:refer|contact|see)", re.IGNORECASE),
        re.compile(r"^if you have further questions", re.IGNORECASE),
        re.compile(r"^the following (?:is|are) (?:the )?details?:?$", re.IGNORECASE),
    ]

    POLICY_KEYWORDS: ClassVar[set[str]] = {
        "attendance",
        "detention",
        "detained",
        "regulation",
        "regulations",
        "r23",
        "r18",
        "r20",
        "cgpa",
        "sgpa",
        "credit",
        "credits",
        "grace",
        "condonation",
        "minimum",
        "percentage",
        "eligibility",
        "eligible",
        "prerequisite",
        "prerequisites",
        "backlog",
        "backlogs",
        "revaluation",
        "malpractice",
    }

    def extract_claims(self, answer_text: str) -> list[ClaimItem]:
        """Extract atomic, verifiable factual propositions from synthesized answer text."""
        if not answer_text or not answer_text.strip():
            return []

        cleaned_text = answer_text.strip()

        # Split into preliminary candidate segments
        raw_segments = self._split_into_sentences(cleaned_text)

        claims: list[ClaimItem] = []
        claim_index = 1

        for raw_seg in raw_segments:
            seg = raw_seg.strip()
            # Strip leading bullet indicators or numbers (e.g., "1.", "•", "-")
            seg = re.sub(r"^(?:[-*•]|\d+\.)\s*", "", seg).strip()

            if not seg or len(seg) < 8 or seg.endswith(":"):
                continue

            # Check if segment matches full sentence discard patterns
            if any(p.search(seg) for p in self.DISCARD_SENTENCE_PATTERNS):
                continue

            # Strip leading meta prefixes
            cleaned_seg = seg
            for prefix_pat in self.META_PREFIX_PATTERNS:
                cleaned_seg = prefix_pat.sub("", cleaned_seg).strip()

            if not cleaned_seg or len(cleaned_seg) < 8 or cleaned_seg.endswith(":"):
                continue

            # Capitalize first letter if needed
            if cleaned_seg and cleaned_seg[0].islower():
                cleaned_seg = cleaned_seg[0].upper() + cleaned_seg[1:]

            # Extract entities using AcademicEntityExtractor
            extracted_ents = AcademicEntityExtractor.extract_entities(cleaned_seg)
            entity_strings = sorted(list({e.raw_entity for e in extracted_ents}))

            # Classify claim
            claim_type = self._classify_claim(cleaned_seg, extracted_ents)

            claim_id = f"claim_{claim_index}"
            claim_item = ClaimItem(
                claim_id=claim_id,
                claim_text=cleaned_seg,
                claim_type=claim_type,
                associated_citation_ids=[],
                is_supported=False,
                support_evidence_chunk_ids=[],
                support_score=0.0,
                entities=entity_strings,
            )
            claims.append(claim_item)
            claim_index += 1

        return claims

    def _split_into_sentences(self, text: str) -> list[str]:
        """Split text into sentences while protecting abbreviations and formatting."""
        norm_text = text.replace("\r\n", "\n")

        # Protect abbreviations by temporarily replacing period with a sentinel token
        protected = norm_text
        abbr_map: dict[str, str] = {}
        for idx, abbr in enumerate(self.PROTECTED_ABBREVIATIONS):
            # Matches e.g. "Prof.", "B.Tech.", "Dr.", "p."
            pattern = re.compile(rf"\b{re.escape(abbr)}\.", re.IGNORECASE)
            for m in pattern.finditer(protected):
                orig = m.group(0)
                placeholder = f"__ABBR_{idx}_{abs(hash(orig)) % 10000}__"
                abbr_map[placeholder] = orig
                protected = protected.replace(orig, placeholder)

        # Protect numeric decimals (e.g. 7.5, 3.14)
        num_pattern = re.compile(r"\b(\d+)\.(\d+)\b")
        protected = num_pattern.sub(r"\1__DOT__\2", protected)

        lines = protected.split("\n")
        raw_sentences: list[str] = []
        sentence_splitter = re.compile(r"(?<=[.?!])\s+(?=[A-Za-z0-9_\"'(\[])")

        for line in lines:
            line_str = line.strip()
            if not line_str:
                continue

            if line_str.startswith("#") or line_str.startswith("===") or line_str.startswith("---"):
                continue

            parts = sentence_splitter.split(line_str)
            for p in parts:
                cleaned_p = p.strip()
                if cleaned_p:
                    # Restore placeholders
                    for ph, orig in abbr_map.items():
                        cleaned_p = cleaned_p.replace(ph, orig)
                    cleaned_p = cleaned_p.replace("__DOT__", ".")
                    raw_sentences.append(cleaned_p)

        return raw_sentences

    def _classify_claim(self, text: str, entities: list) -> ClaimType:
        """Classify claim into 'date', 'policy', 'factual', or 'general'."""
        text_lower = text.lower()

        # Check for date entities or explicit calendar dates
        has_date_entity = any(e.entity_type in {"date", "academic_year", "exam_type"} for e in entities)
        if has_date_entity or re.search(r"\b(?:january|february|march|april|may|june|july|august|september|october|november|december)\b", text_lower):
            return "date"

        # Check for regulation / policy content
        has_reg_entity = any(e.entity_type == "regulation" for e in entities)
        has_policy_kw = any(kw in text_lower for kw in self.POLICY_KEYWORDS) or "%" in text
        if has_reg_entity or has_policy_kw:
            return "policy"

        # Check for course codes or explicit factual university entities
        has_course_entity = any(e.entity_type == "course_code" for e in entities)
        if has_course_entity or re.search(r"\b(?:syllabus|credit|department|laboratory|prerequisite|curriculum)\b", text_lower):
            return "factual"

        return "general"
