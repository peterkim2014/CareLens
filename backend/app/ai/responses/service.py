from app.ai.generation import GroundedResponse
from app.ai.responses.schemas import (
    UserResponse,
    UserResponseKind,
)


class UserResponseService:
    def for_emergency(self) -> UserResponse:
        return UserResponse(
            kind=UserResponseKind.EMERGENCY,
            message=(
                "Your symptoms may represent a medical emergency. "
                "Seek emergency medical care immediately."
            ),
            recommended_actions=[
                "Call your local emergency number now.",
                (
                    "Do not drive yourself if you feel faint, weak, "
                    "confused, or unable to breathe normally."
                ),
                ("Stay with another person when possible while waiting for help."),
            ],
            can_continue=False,
        )

    def for_urgent(self) -> UserResponse:
        return UserResponse(
            kind=UserResponseKind.URGENT,
            message=(
                "Your symptoms may require prompt medical evaluation. "
                "Contact a qualified healthcare professional as soon "
                "as possible."
            ),
            recommended_actions=[
                (
                    "Contact your doctor, an urgent care clinic, or "
                    "another qualified healthcare professional."
                ),
                (
                    "Seek emergency care if your symptoms become severe "
                    "or rapidly worsen."
                ),
            ],
            can_continue=False,
        )

    def for_grounded_response(
        self,
        grounded_response: GroundedResponse,
    ) -> UserResponse:
        return UserResponse(
            kind=UserResponseKind.GROUNDED,
            message=grounded_response.answer,
            recommended_actions=[
                *grounded_response.limitations,
            ],
            can_continue=True,
        )

    def for_insufficient_evidence(self) -> UserResponse:
        return UserResponse(
            kind=UserResponseKind.INSUFFICIENT_EVIDENCE,
            message=(
                "I do not have enough reliable evidence to answer this question safely."
            ),
            recommended_actions=[
                (
                    "Provide more detail about the symptoms, their "
                    "duration, and their severity."
                ),
                (
                    "Consult a qualified healthcare professional for "
                    "personal medical guidance."
                ),
            ],
            can_continue=True,
        )

    def for_rejected_response(self) -> UserResponse:
        return UserResponse(
            kind=UserResponseKind.RESPONSE_REJECTED,
            message=(
                "I could not verify that the generated response was "
                "fully supported by the available evidence."
            ),
            recommended_actions=[
                ("Rephrase the question or provide additional clinical context."),
                (
                    "Consult a qualified healthcare professional if "
                    "you need medical guidance."
                ),
            ],
            can_continue=True,
        )
