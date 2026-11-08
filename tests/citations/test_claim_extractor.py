"""Unit tests for ClaimExtractor (sentence splitting, abbreviation protection, entity identification)."""

from citations.claim_extractor import ClaimExtractor


def test_claim_extractor_abbreviation_preservation() -> None:
    """Verify that abbreviations like Dr., Prof., B.Tech., p., etc. do not cause false sentence splits."""
    extractor = ClaimExtractor()
    text = (
        "Prof. Sharma announced that B.Tech. CSE Mid-Semester Examination I begins on 12 September 2026. "
        "Dr. Rao confirmed the schedule on p. 3 of the notice."
    )
    claims = extractor.extract_claims(text)

    # Should be exactly 2 claims, not split at Prof., B.Tech., Dr., or p.
    assert len(claims) == 2
    assert "Prof. Sharma" in claims[0].claim_text
    assert "B.Tech." in claims[0].claim_text
    assert "Dr. Rao" in claims[1].claim_text
    assert "p. 3" in claims[1].claim_text


def test_claim_extractor_strips_meta_framing() -> None:
    """Verify conversational and meta prefixes are stripped from claims."""
    extractor = ClaimExtractor()
    text = (
        "Based on the provided documents, the examination starts on 12 September 2026. "
        "According to the official regulations, students need 75% attendance. "
        "Here is the information: Course 23CSE302T covers Machine Learning."
    )
    claims = extractor.extract_claims(text)

    assert len(claims) == 3
    # Check that meta prefixes were stripped
    assert not claims[0].claim_text.lower().startswith("based on the provided")
    assert not claims[1].claim_text.lower().startswith("according to the official")
    assert not claims[2].claim_text.lower().startswith("here is the information")
    assert "examination starts on 12 september 2026" in claims[0].claim_text.lower()
    assert "students need 75% attendance" in claims[1].claim_text.lower()
    assert "23cse302t" in claims[2].claim_text.lower()


def test_claim_extractor_discards_conversational_filler() -> None:
    """Verify conversational closing lines are discarded entirely."""
    extractor = ClaimExtractor()
    text = (
        "Mid-Semester Examination I is on 12 September 2026.\n"
        "I hope this information helps!\n"
        "Please let me know if you have further questions."
    )
    claims = extractor.extract_claims(text)
    assert len(claims) == 1
    assert "12 September 2026" in claims[0].claim_text


def test_claim_extractor_classification() -> None:
    """Verify claim classification into date, policy, factual, and general types."""
    extractor = ClaimExtractor()

    date_text = "Mid-Semester Examination I is scheduled for 12 September 2026."
    claims_date = extractor.extract_claims(date_text)
    assert len(claims_date) == 1
    assert claims_date[0].claim_type == "date"

    policy_text = "Under regulation R23, students must maintain 75% attendance."
    claims_policy = extractor.extract_claims(policy_text)
    assert len(claims_policy) == 1
    assert claims_policy[0].claim_type == "policy"

    factual_text = "Course 23CSE302T covers advanced data structures and algorithms."
    claims_factual = extractor.extract_claims(factual_text)
    assert len(claims_factual) == 1
    assert claims_factual[0].claim_type == "factual"


def test_claim_extractor_deterministic_ids() -> None:
    """Verify that claims receive deterministic sequential IDs."""
    extractor = ClaimExtractor()
    text = "Sentence one. Sentence two. Sentence three."
    claims = extractor.extract_claims(text)
    assert len(claims) == 3
    assert [c.claim_id for c in claims] == ["claim_1", "claim_2", "claim_3"]


def test_claim_extractor_empty_or_fallback() -> None:
    """Verify fallback response produces zero claims."""
    extractor = ClaimExtractor()
    assert extractor.extract_claims("") == []
    assert extractor.extract_claims("   ") == []
    fallback = "I couldn't find sufficient information in the available SR University documents to answer this accurately."
    assert extractor.extract_claims(fallback) == []
