"""Deterministic cross-document institutional conflict detection.

Inspects retrieved generation evidence to identify factual contradictions
(date discrepancies, regulation discrepancies, policy discrepancies)
across multiple sources without silently picking a winner.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass

from generation.grounding.entities import AcademicEntityExtractor
from generation.models import ConflictReport, RetrievedEvidence


@dataclass(frozen=True)
class FactAssertion:
    """Represents an extracted factual claim aligned with an institutional entity and attribute."""

    entity_subject: str
    attribute: str
    value: str
    raw_text: str
    source_name: str


class ConflictDetector:
    """Detects factual discrepancies across retrieved institutional evidence documents.

    Conservative rule-based alignment:
    - Compares facts only when the subject and attribute are strictly aligned.
    - Never flags different events (e.g. Mid-I vs Mid-II exams) as conflicting dates.
    - Surfaces discrepancies rather than silently fabricating or resolving them.
    """

    ATTENDANCE_PATTERN = re.compile(r"\b(?:minimum\s+attendance|attendance\s+requirement)\b[^\d]*(\d{2})%", re.IGNORECASE)

    def detect_conflicts(self, evidence_items: Sequence[RetrievedEvidence]) -> ConflictReport:
        """Analyze evidence items and return a structured ConflictReport."""
        if len(evidence_items) < 2:
            return ConflictReport(
                has_conflict=False,
                conflict_type=None,
                conflicting_sources=[],
                details=[],
            )

        assertions = self._extract_assertions(evidence_items)
        if not assertions:
            return ConflictReport(has_conflict=False)

        # Group assertions by (entity_subject, attribute)
        grouped: dict[tuple[str, str], list[FactAssertion]] = {}
        for a in assertions:
            key = (a.entity_subject, a.attribute)
            grouped.setdefault(key, []).append(a)

        discrepancies: list[dict[str, object]] = []

        for (subj, attr), claims in grouped.items():
            # Check if there are different sources asserting differing values
            sources = {c.source_name for c in claims}
            if len(sources) < 2:
                # Claims come from the same source; no cross-document conflict
                continue

            unique_values = {c.value for c in claims}
            if len(unique_values) > 1:
                # Discrepancy detected across sources!
                conflicting_sources = sorted(sources)
                detail_lines = []
                for c in claims:
                    detail_lines.append(f"[{c.source_name}]: {subj} {attr} is '{c.value}' ({c.raw_text.strip()})")

                conflict_type = self._classify_conflict_type(attr)
                discrepancies.append({
                    "type": conflict_type,
                    "sources": conflicting_sources,
                    "details": detail_lines,
                })

        if not discrepancies:
            return ConflictReport(
                has_conflict=False,
                conflict_type=None,
                conflicting_sources=[],
                details=[],
            )

        # Take primary discrepancy
        primary = discrepancies[0]
        all_sources = sorted({s for d in discrepancies for s in d["sources"]})  # type: ignore
        all_details = [line for d in discrepancies for line in d["details"]]  # type: ignore

        return ConflictReport(
            has_conflict=True,
            conflict_type=str(primary["type"]),
            conflicting_sources=all_sources,
            details=all_details,
        )

    def _extract_assertions(self, evidence_items: Sequence[RetrievedEvidence]) -> list[FactAssertion]:
        """Extract structured assertions from evidence chunks."""
        assertions: list[FactAssertion] = []

        for ev in evidence_items:
            source = ev.document_name or "Unknown Source"
            text = ev.text

            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line or line.startswith("###"):
                    continue

                entities = AcademicEntityExtractor.extract_entities(line)
                course_codes = [e for e in entities if e.entity_type == "course_code"]
                dates = [e for e in entities if e.entity_type == "date"]
                regulations = [e for e in entities if e.entity_type == "regulation"]
                exam_types = [e for e in entities if e.entity_type == "exam_type"]

                # 1. Examination date assertion:
                # E.g., Mid-Semester Examination-I: 12 September 2026 to 16 September 2026
                if exam_types and dates:
                    for ex in exam_types:
                        for dt in dates:
                            assertions.append(FactAssertion(
                                entity_subject=ex.normalized_entity,
                                attribute="examination_date",
                                value=dt.normalized_entity,
                                raw_text=line,
                                source_name=source,
                            ))

                # 2. Course regulation assertion:
                # E.g., Course 23CSE302T is offered under Regulation R23
                if course_codes and regulations:
                    for cc in course_codes:
                        for reg in regulations:
                            assertions.append(FactAssertion(
                                entity_subject=cc.normalized_entity,
                                attribute="regulation",
                                value=reg.normalized_entity,
                                raw_text=line,
                                source_name=source,
                            ))

                # 3. Policy assertion (e.g. minimum attendance percentage):
                att_match = self.ATTENDANCE_PATTERN.search(line)
                if att_match:
                    pct = att_match.group(1)
                    assertions.append(FactAssertion(
                        entity_subject="attendance",
                        attribute="minimum_percentage",
                        value=f"{pct}%",
                        raw_text=line,
                        source_name=source,
                    ))

        return assertions

    @staticmethod
    def _classify_conflict_type(attribute: str) -> str:
        """Map attribute to canonical conflict type."""
        if "date" in attribute:
            return "date_discrepancy"
        if "regulation" in attribute:
            return "regulation_discrepancy"
        return "policy_discrepancy"
