from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.ai.generation import GroundedResponse
from app.ai.intake import ClinicalQuery, RiskAssessment
from app.ai.observability import PipelineAudit
from app.ai.responses import UserResponse
from app.ai.retrieval import RetrievalResult
from app.ai.validation import GroundingValidationResult


class AnalysisDisposition(StrEnum):
    HALTED_EMERGENCY = "halted_emergency"
    HALTED_URGENT = "halted_urgent"
    RESPONSE_GENERATED = "response_generated"
    RESPONSE_REJECTED = "response_rejected"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"


class PipelineStage(StrEnum):
    INTAKE_VALIDATED = "intake_validated"
    RISK_ASSESSED = "risk_assessed"
    SAFETY_ROUTED = "safety_routed"
    EVIDENCE_RETRIEVED = "evidence_retrieved"
    EVIDENCE_VALIDATED = "evidence_validated"
    RESPONSE_GENERATED = "response_generated"
    RESPONSE_VALIDATED = "response_validated"
    USER_RESPONSE_CREATED = "user_response_created"


class AnalysisResult(BaseModel):
    trace_id: UUID
    query: ClinicalQuery
    risk_assessment: RiskAssessment
    disposition: AnalysisDisposition
    completed_stages: list[PipelineStage]
    retrieval_result: RetrievalResult | None
    grounded_response: GroundedResponse | None
    grounding_validation: GroundingValidationResult | None
    user_response: UserResponse
    audit: PipelineAudit
