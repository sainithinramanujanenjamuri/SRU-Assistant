"""Unit tests for AcademicLexicalTokenizer preserving university academic identifiers."""

import pytest

from retrieval.lexical.tokenizer import AcademicLexicalTokenizer


@pytest.fixture
def tokenizer() -> AcademicLexicalTokenizer:
    return AcademicLexicalTokenizer()


def test_tokenizer_preserves_course_codes(tokenizer: AcademicLexicalTokenizer):
    """Course codes such as 23CSE302T must remain intact as single tokens."""
    tokens = tokenizer.tokenize("The syllabus for 23CSE302T covers algorithms.")
    assert "23cse302t" in tokens
    assert "algorithms" in tokens
    assert "the" not in tokens  # Stop word removed


def test_tokenizer_preserves_regulation_identifiers(tokenizer: AcademicLexicalTokenizer):
    """Regulation identifiers such as R23 must remain intact."""
    tokens = tokenizer.tokenize("Students admitted under R23 and R20 regulations.")
    assert "r23" in tokens
    assert "r20" in tokens
    assert "regulations" in tokens


def test_tokenizer_preserves_academic_years(tokenizer: AcademicLexicalTokenizer):
    """Hyphenated academic sessions like 2026-27 and 2025-2026 must remain intact."""
    tokens = tokenizer.tokenize("Academic Calendar for 2026-27 session and 2025-2026.")
    assert "2026-27" in tokens
    assert "2025-2026" in tokens
    assert "calendar" in tokens


def test_tokenizer_preserves_dates(tokenizer: AcademicLexicalTokenizer):
    """Exact date formats like 12 September 2026 must be cleanly tokenized."""
    tokens = tokenizer.tokenize("Examinations begin on 12 September 2026.")
    assert "12" in tokens
    assert "september" in tokens
    assert "2026" in tokens
    assert "examinations" in tokens


def test_tokenizer_preserves_hyphenated_terms_and_acronyms(tokenizer: AcademicLexicalTokenizer):
    """Hyphenated terms (Mid-Semester) and dot abbreviations (B.Tech) must be preserved."""
    tokens = tokenizer.tokenize("Mid-Semester examinations for B.Tech in CSE.")
    assert "mid-semester" in tokens
    assert "b.tech" in tokens
    assert "cse" in tokens


def test_tokenizer_handles_mixed_case(tokenizer: AcademicLexicalTokenizer):
    """Lowercasing should normalize mixed case while preserving exact code structure."""
    tokens1 = tokenizer.tokenize("23CSE302T")
    tokens2 = tokenizer.tokenize("23cse302t")
    tokens3 = tokenizer.tokenize("23Cse302t")
    assert tokens1 == tokens2 == tokens3 == ["23cse302t"]


def test_tokenizer_edge_cases(tokenizer: AcademicLexicalTokenizer):
    """Empty string, whitespace, punctuation, and stop-word only inputs."""
    assert tokenizer.tokenize("") == []
    assert tokenizer.tokenize("   ") == []
    assert tokenizer.tokenize("!!! ??? ... ,,, ;;;") == []
    # Stop words only
    assert tokenizer.tokenize("this is the and or but") == []
    # Stop word with digit or hyphen must NOT be dropped
    tokens = tokenizer.tokenize("is-12")
    assert "is-12" in tokens
    assert "12" in tokens


def test_tokenizer_manifest_version(tokenizer: AcademicLexicalTokenizer):
    """Tokenizer must report a valid non-empty version string for manifest validation."""
    assert tokenizer.version == "1.0.0"
