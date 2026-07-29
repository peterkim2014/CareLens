import pytest

from app.ai.intake import (
    ClinicalQuery,
    RiskClassifier,
    RiskLevel,
    RoutingAction,
)


@pytest.fixture
def classifier() -> RiskClassifier:
    return RiskClassifier()


@pytest.mark.parametrize(
    ("text", "expected_code"),
    [
        ("I have severe chest pain.", "chest_pain"),
        ("I can't breathe properly.", "breathing_difficulty"),
        ("My speech is slurred and one side feels weak.", "stroke_signs"),
        ("They are unconscious and not waking up.", "unconsciousness"),
        ("The wound is bleeding heavily.", "severe_bleeding"),
        ("I want to kill myself.", "self_harm"),
    ],
)
def test_emergency_signals_are_classified(
    classifier: RiskClassifier,
    text: str,
    expected_code: str,
) -> None:
    assessment = classifier.classify(ClinicalQuery(text=text))

    assert assessment.risk_level is RiskLevel.EMERGENCY
    assert assessment.routing_action is RoutingAction.SEEK_EMERGENCY_CARE
    assert assessment.emergency_message is not None
    assert expected_code in {signal.code for signal in assessment.signals}


@pytest.mark.parametrize(
    "text",
    [
        "I have a high fever.",
        "I cannot keep water down.",
        "My symptoms are getting worse quickly.",
    ],
)
def test_urgent_signals_are_classified(
    classifier: RiskClassifier,
    text: str,
) -> None:
    assessment = classifier.classify(ClinicalQuery(text=text))

    assert assessment.risk_level is RiskLevel.URGENT
    assert assessment.routing_action is RoutingAction.SEEK_PROMPT_CARE
    assert assessment.signals
    assert assessment.emergency_message is None


def test_routine_query_continues_to_analysis(
    classifier: RiskClassifier,
) -> None:
    assessment = classifier.classify(
        ClinicalQuery(text="What are common causes of seasonal allergies?")
    )

    assert assessment.risk_level is RiskLevel.ROUTINE
    assert assessment.routing_action is RoutingAction.CONTINUE_ANALYSIS
    assert assessment.signals == []
    assert assessment.emergency_message is None


def test_query_whitespace_is_normalized() -> None:
    query = ClinicalQuery(text="  What   causes   headaches?  ")

    assert query.text == "What causes headaches?"
