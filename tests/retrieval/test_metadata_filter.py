"""Unit tests for MetadataFilter and null-safe institutional evidence preservation."""

import pytest

from retrieval.filtering.metadata_filter import MetadataFilter
from retrieval.models import FilterError, HybridSearchResult


def make_cand(chunk_id: str, score: float, metadata: dict) -> HybridSearchResult:
    return HybridSearchResult(
        chunk_id=chunk_id,
        document_id="doc_" + chunk_id,
        text="Sample text for " + chunk_id,
        fused_score=score,
        normalized_fused_score=score,
        metadata=metadata,
        provenance={"source_file": "test.pdf"},
    )


@pytest.fixture
def test_candidates() -> list[HybridSearchResult]:
    return [
        # 1. Global university-wide document (calendar): department is explicitly None
        make_cand(
            chunk_id="cal_chunk_0",
            score=0.70,
            metadata={
                "document_name": "calendar.txt",
                "department": None,
                "program": None,
                "academic_year": "2026-27",
            },
        ),
        # 2. CSE-specific document: department is Computer Science and Engineering
        make_cand(
            chunk_id="cse_chunk_0",
            score=0.60,
            metadata={
                "document_name": "cse_syllabus.pdf",
                "department": "Computer Science and Engineering",
                "program": "B.Tech",
                "semester": "Semester VII",
            },
        ),
        # 3. ECE-specific document: department is Electronics and Communication Engineering
        make_cand(
            chunk_id="ece_chunk_0",
            score=0.65,
            metadata={
                "document_name": "ece_syllabus.pdf",
                "department": "Electronics and Communication Engineering",
                "program": "B.Tech",
                "semester": "Semester VII",
            },
        ),
        # 4. Unknown metadata document: missing 'department' key entirely
        make_cand(
            chunk_id="unk_chunk_0",
            score=0.50,
            metadata={
                "document_name": "general_notice.txt",
                "academic_year": "2026-27",
            },
        ),
    ]


def test_null_safe_global_preservation_cse_query(test_candidates: list[HybridSearchResult]):
    """Global calendar with department=None MUST survive department=CSE filter."""
    flt = MetadataFilter(mode="hard")
    results = flt.filter_candidates(test_candidates, filters={"department": "CSE"})
    result_ids = [r.chunk_id for r in results]

    # Global calendar AND CSE syllabus must be present
    assert "cal_chunk_0" in result_ids, "Global document with department=None must not be pruned"
    assert "cse_chunk_0" in result_ids, "CSE document must match CSE filter"
    # ECE document must be pruned
    assert "ece_chunk_0" not in result_ids, "ECE document must be filtered out for CSE query"


def test_null_safe_global_preservation_mtech_query(test_candidates: list[HybridSearchResult]):
    """Global calendar with program=None MUST survive program=M.Tech filter."""
    flt = MetadataFilter(mode="hard")
    results = flt.filter_candidates(test_candidates, filters={"program": "M.Tech"})
    result_ids = [r.chunk_id for r in results]

    assert "cal_chunk_0" in result_ids, "Global calendar must survive program filtering"
    assert "cse_chunk_0" not in result_ids, "B.Tech syllabus must be pruned for M.Tech query"


def test_soft_filtering_boost_and_penalty(test_candidates: list[HybridSearchResult]):
    """In soft mode: match gets +0.15, global gets 0.0, non-global mismatch gets -0.15."""
    flt = MetadataFilter(mode="soft", boost=0.15, penalty=0.15)
    results = flt.filter_candidates(test_candidates, filters={"department": "CSE"})

    res_map = {r.chunk_id: r.normalized_score for r in results}

    # CSE syllabus: base 0.60 + 0.15 = 0.75
    assert res_map["cse_chunk_0"] == pytest.approx(0.75, abs=1e-4)
    # Global calendar: base 0.70 + 0.0 (global no penalty) = 0.70
    assert res_map["cal_chunk_0"] == pytest.approx(0.70, abs=1e-4)
    # ECE syllabus: base 0.65 - 0.15 = 0.50
    assert res_map["ece_chunk_0"] == pytest.approx(0.50, abs=1e-4)
    # Unknown metadata: base 0.50 + 0.0 (missing neutral) = 0.50
    assert res_map["unk_chunk_0"] == pytest.approx(0.50, abs=1e-4)

    # Deterministic sorting: cse_chunk_0 (0.75) > cal_chunk_0 (0.70) > ece_chunk_0 (0.50, id 'ece...') > unk_chunk_0
    assert results[0].chunk_id == "cse_chunk_0"
    assert results[1].chunk_id == "cal_chunk_0"


def test_soft_filter_score_bounds():
    """Soft filtering scores must never exceed 1.0 or fall below 0.0."""
    high_cand = make_cand("high", 0.95, {"department": "Computer Science and Engineering"})
    low_cand = make_cand("low", 0.05, {"department": "Mechanical Engineering"})

    flt = MetadataFilter(mode="soft", boost=0.20, penalty=0.20)
    results = flt.filter_candidates([high_cand, low_cand], filters={"department": "CSE"})

    res_map = {r.chunk_id: r.normalized_score for r in results}
    assert res_map["high"] <= 1.0
    assert res_map["low"] >= 0.0


def test_alias_normalization(test_candidates: list[HybridSearchResult]):
    flt = MetadataFilter(mode="hard")

    # 'CSE' matches 'Computer Science and Engineering'
    r1 = flt.filter_candidates(test_candidates, filters={"department": "CSE"})
    r2 = flt.filter_candidates(test_candidates, filters={"department": "Computer Science and Engineering"})
    assert [x.chunk_id for x in r1] == [x.chunk_id for x in r2]

    # 'VII' matches 'Semester VII'
    r3 = flt.filter_candidates(test_candidates, filters={"semester": "VII"})
    r4 = flt.filter_candidates(test_candidates, filters={"semester": "7"})
    r5 = flt.filter_candidates(test_candidates, filters={"semester": "Semester VII"})
    assert [x.chunk_id for x in r3] == [x.chunk_id for x in r4] == [x.chunk_id for x in r5]


def test_multiple_constraints(test_candidates: list[HybridSearchResult]):
    flt = MetadataFilter(mode="hard")
    # Both department=CSE and semester=Semester VII
    results = flt.filter_candidates(
        test_candidates,
        filters={"department": "CSE", "semester": "Semester VII"},
    )
    result_ids = [r.chunk_id for r in results]
    # Global calendar has semester=None (or missing), so it survives; cse_chunk_0 matches both
    assert "cse_chunk_0" in result_ids
    assert "cal_chunk_0" in result_ids
    assert "ece_chunk_0" not in result_ids


def test_empty_candidates_returns_empty():
    flt = MetadataFilter(mode="hard")
    assert flt.filter_candidates([], filters={"department": "CSE"}) == []


def test_invalid_filter_mode_raises_error():
    with pytest.raises(FilterError):
        MetadataFilter(mode="unsupported_mode")
