from app.ai.generation import (
    EvidenceCitation,
    GroundedResponse,
)
from app.ai.responses import (
    UserResponseKind,
    UserResponseService,
)


def test_service_creates_emergency_response() -> None:
    service = UserResponseService()

    response = service.for_emergency()

    assert response.kind is UserResponseKind.EMERGENCY
    assert response.can_continue is False
    assert "emergency" in response.message.lower()
    assert response.recommended_actions


def test_service_creates_urgent_response() -> None:
    service = UserResponseService()

    response = service.for_urgent()

    assert response.kind is UserResponseKind.URGENT
    assert response.can_continue is False
    assert "prompt medical evaluation" in response.message.lower()
    assert response.recommended_actions


def test_service_creates_grounded_response() -> None:
    service = UserResponseService()

    grounded_response = GroundedResponse(
        answer="Seasonal allergies may cause sneezing. [1]",
        citations=[
            EvidenceCitation(
                citation_id=1,
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                source="Clinical Reference",
            )
        ],
        limitations=["This response is not a medical diagnosis."],
    )

    response = service.for_grounded_response(grounded_response)

    assert response.kind is UserResponseKind.GROUNDED
    assert response.can_continue is True
    assert response.message == grounded_response.answer
    assert response.recommended_actions == (grounded_response.limitations)


def test_service_creates_insufficient_evidence_response() -> None:
    service = UserResponseService()

    response = service.for_insufficient_evidence()

    assert response.kind is UserResponseKind.INSUFFICIENT_EVIDENCE
    assert response.can_continue is True
    assert "enough reliable evidence" in response.message
    assert response.recommended_actions


def test_service_creates_rejected_response() -> None:
    service = UserResponseService()

    response = service.for_rejected_response()

    assert response.kind is UserResponseKind.RESPONSE_REJECTED
    assert response.can_continue is True
    assert "fully supported" in response.message
    assert response.recommended_actions
