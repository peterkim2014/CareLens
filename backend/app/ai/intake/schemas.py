from enum import StrEnum

from pydantic import BaseModel, Field, field_validator


class RiskLevel(StrEnum):
    ROUTINE = "routine"
    URGENT = "urgent"
    EMERGENCY = "emergency"


class RoutingAction(StrEnum):
    CONTINUE_ANALYSIS = "continue_analysis"
    SEEK_PROMPT_CARE = "seek_prompt_care"
    SEEK_EMERGENCY_CARE = "seek_emergency_care"


class ClinicalQuery(BaseModel):
    text: str = Field(
        min_length=3,
        max_length=5_000,
        description="User-provided medical question or symptom description.",
    )

    @field_validator("text")
    @classmethod
    def normalize_text(cls, value: str) -> str:
        normalized = " ".join(value.split())

        if not normalized:
            raise ValueError("Query text cannot be empty.")

        return normalized


class RiskSignal(BaseModel):
    code: str
    label: str
    matched_phrase: str
    risk_level: RiskLevel


class RiskAssessment(BaseModel):
    risk_level: RiskLevel
    routing_action: RoutingAction
    signals: list[RiskSignal]
    reasoning: list[str]
    emergency_message: str | None = None
