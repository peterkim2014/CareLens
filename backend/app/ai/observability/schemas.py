from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

AuditMetadataValue = str | int | float | bool


class PipelineEventStatus(StrEnum):
    COMPLETED = "completed"
    FAILED = "failed"


class PipelineEvent(BaseModel):
    stage: str = Field(min_length=1)
    status: PipelineEventStatus
    started_at: datetime
    completed_at: datetime
    duration_ms: float = Field(ge=0)
    metadata: dict[str, AuditMetadataValue] = Field(default_factory=dict)


class PipelineAudit(BaseModel):
    started_at: datetime
    completed_at: datetime
    total_duration_ms: float = Field(ge=0)
    events: list[PipelineEvent] = Field(default_factory=list)
