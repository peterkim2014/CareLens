import pytest

from app.ai.retrieval.scoring import (
    WeightedTextField,
    lexical_score,
    tokenize,
    weighted_lexical_score,
)


def test_tokenize_normalizes_case() -> None:
    assert tokenize("Sneezing SNEEZING") == {"sneezing"}


def test_tokenize_removes_punctuation() -> None:
    assert tokenize("sneezing, itchy eyes!") == {
        "sneezing",
        "itchy",
        "eyes",
    }


def test_tokenize_removes_stopwords() -> None:
    assert tokenize("I have sneezing and itchy eyes") == {
        "sneezing",
        "itchy",
        "eyes",
    }


def test_tokenize_ignores_short_tokens() -> None:
    assert tokenize("a x sneezing") == {"sneezing"}


def test_lexical_score_returns_matching_terms() -> None:
    score, matched_terms = lexical_score(
        "Sneezing and itchy eyes",
        ("Seasonal allergies commonly cause sneezing and itchy eyes."),
    )

    assert score == pytest.approx(1.0)
    assert matched_terms == [
        "eyes",
        "itchy",
        "sneezing",
    ]


def test_lexical_score_ignores_stopword_matches() -> None:
    score, matched_terms = lexical_score(
        "Sneezing and itchy eyes",
        ("Stress and insufficient sleep may cause headaches."),
    )

    assert score == 0.0
    assert matched_terms == []


def test_lexical_score_returns_zero_for_empty_query() -> None:
    score, matched_terms = lexical_score(
        "",
        "Seasonal allergy symptoms",
    )

    assert score == 0.0
    assert matched_terms == []


def test_lexical_score_returns_zero_for_stopword_query() -> None:
    score, matched_terms = lexical_score(
        "What is it and how does it work?",
        "Unrelated medical evidence.",
    )

    assert score == 0.0
    assert matched_terms == []


def test_weighted_score_prefers_stronger_field() -> None:
    title_score, _ = weighted_lexical_score(
        "seasonal allergies",
        fields=(
            WeightedTextField(
                text="Seasonal allergies",
                weight=1.0,
            ),
        ),
    )

    content_score, _ = weighted_lexical_score(
        "seasonal allergies",
        fields=(
            WeightedTextField(
                text="Seasonal allergies",
                weight=0.6,
            ),
        ),
    )

    assert title_score > content_score


def test_weighted_score_uses_highest_term_weight() -> None:
    score, matched_terms = weighted_lexical_score(
        "sneezing",
        fields=(
            WeightedTextField(
                text="Sneezing",
                weight=0.6,
            ),
            WeightedTextField(
                text="Sneezing",
                weight=0.9,
            ),
        ),
    )

    assert score == pytest.approx(0.9)
    assert matched_terms == ["sneezing"]


def test_weighted_score_combines_field_matches() -> None:
    score, matched_terms = weighted_lexical_score(
        "seasonal allergies",
        fields=(
            WeightedTextField(
                text="Seasonal",
                weight=1.0,
            ),
            WeightedTextField(
                text="Allergies",
                weight=0.9,
            ),
        ),
    )

    assert score == pytest.approx(0.95)
    assert matched_terms == [
        "allergies",
        "seasonal",
    ]


def test_weighted_score_rejects_invalid_weight() -> None:
    with pytest.raises(
        ValueError,
        match="Field weights",
    ):
        weighted_lexical_score(
            "headache",
            fields=(
                WeightedTextField(
                    text="headache",
                    weight=1.5,
                ),
            ),
        )
