from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field


class APIErrorCode(StrEnum):
    ANALYSIS_PIPELINE_FAILED = "analysis_pipeline_failed"


class APIErrorDetail(BaseModel):
    code: APIErrorCode
    message: str = Field(min_length=1)
    trace_id: UUID
    failed_stage: str = Field(min_length=1)
    retryable: bool


class APIErrorResponse(BaseModel):
    error: APIErrorDetail
