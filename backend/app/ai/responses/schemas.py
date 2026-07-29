from enum import StrEnum

from pydantic import BaseModel, Field


class UserResponseKind(StrEnum):
    EMERGENCY = "emergency"
    URGENT = "urgent"
    GROUNDED = "grounded"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    RESPONSE_REJECTED = "response_rejected"


class UserResponse(BaseModel):
    kind: UserResponseKind
    message: str = Field(min_length=1)
    recommended_actions: list[str] = Field(default_factory=list)
    can_continue: bool
