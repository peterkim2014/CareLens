from uuid import UUID, uuid4

from app.ai.generation import GroundedResponseService
from app.ai.intake import (
    ClinicalQuery,
    RiskAssessment,
    RiskClassifier,
    RiskLevel,
)
from app.ai.observability import PipelineAuditRecorder
from app.ai.pipeline.schemas import (
    AnalysisDisposition,
    AnalysisResult,
    PipelineStage,
)
from app.ai.responses import UserResponseService
from app.ai.retrieval import RetrievalService
from app.ai.validation import GroundingValidator
from app.core.errors import AnalysisPipelineError
from app.core.telemetry import get_trace_id


class AnalysisPipeline:
    def __init__(
        self,
        risk_classifier: RiskClassifier,
        retrieval_service: RetrievalService,
        response_service: GroundedResponseService,
        grounding_validator: GroundingValidator,
        user_response_service: UserResponseService,
    ) -> None:
        self._risk_classifier = risk_classifier
        self._retrieval_service = retrieval_service
        self._response_service = response_service
        self._grounding_validator = grounding_validator
        self._user_response_service = user_response_service

    def run(self, query: ClinicalQuery) -> AnalysisResult:
        trace_id = get_trace_id() or uuid4()
        recorder = PipelineAuditRecorder()
        completed_stages: list[PipelineStage] = []

        intake_timer = recorder.start_stage()
        completed_stages.append(PipelineStage.INTAKE_VALIDATED)
        recorder.complete_stage(
            stage=PipelineStage.INTAKE_VALIDATED.value,
            timer=intake_timer,
        )

        risk_timer = recorder.start_stage()

        try:
            risk_assessment = self._risk_classifier.classify(query)
        except Exception as error:
            failed_stage = PipelineStage.RISK_ASSESSED.value

            recorder.fail_stage(
                stage=failed_stage,
                timer=risk_timer,
                error_type=type(error).__name__,
            )

            raise AnalysisPipelineError(
                trace_id=trace_id,
                failed_stage=failed_stage,
                audit=recorder.build(),
                retryable=False,
            ) from error

        completed_stages.append(PipelineStage.RISK_ASSESSED)
        recorder.complete_stage(
            stage=PipelineStage.RISK_ASSESSED.value,
            timer=risk_timer,
            metadata={
                "risk_level": risk_assessment.risk_level.value,
                "signal_count": len(risk_assessment.signals),
            },
        )

        safety_timer = recorder.start_stage()
        completed_stages.append(PipelineStage.SAFETY_ROUTED)
        recorder.complete_stage(
            stage=PipelineStage.SAFETY_ROUTED.value,
            timer=safety_timer,
            metadata={
                "routing_action": risk_assessment.routing_action.value,
            },
        )

        if risk_assessment.risk_level is RiskLevel.EMERGENCY:
            return self._build_emergency_result(
                trace_id=trace_id,
                query=query,
                risk_assessment=risk_assessment,
                completed_stages=completed_stages,
                recorder=recorder,
            )

        if risk_assessment.risk_level is RiskLevel.URGENT:
            return self._build_urgent_result(
                trace_id=trace_id,
                query=query,
                risk_assessment=risk_assessment,
                completed_stages=completed_stages,
                recorder=recorder,
            )

        retrieval_timer = recorder.start_stage()

        try:
            retrieval_result = self._retrieval_service.retrieve(query.text)
        except Exception as error:
            failed_stage = PipelineStage.EVIDENCE_RETRIEVED.value

            recorder.fail_stage(
                stage=failed_stage,
                timer=retrieval_timer,
                error_type=type(error).__name__,
            )

            raise AnalysisPipelineError(
                trace_id=trace_id,
                failed_stage=failed_stage,
                audit=recorder.build(),
                retryable=True,
            ) from error

        completed_stages.append(PipelineStage.EVIDENCE_RETRIEVED)
        recorder.complete_stage(
            stage=PipelineStage.EVIDENCE_RETRIEVED.value,
            timer=retrieval_timer,
            metadata={
                "evidence_count": len(retrieval_result.evidence),
                "total_candidates": retrieval_result.total_candidates,
            },
        )

        validation_timer = recorder.start_stage()
        evidence_is_sufficient = bool(retrieval_result.evidence)

        completed_stages.append(PipelineStage.EVIDENCE_VALIDATED)
        recorder.complete_stage(
            stage=PipelineStage.EVIDENCE_VALIDATED.value,
            timer=validation_timer,
            metadata={
                "is_sufficient": evidence_is_sufficient,
            },
        )

        if not evidence_is_sufficient:
            user_response_timer = recorder.start_stage()
            user_response = self._user_response_service.for_insufficient_evidence()

            completed_stages.append(PipelineStage.USER_RESPONSE_CREATED)
            recorder.complete_stage(
                stage=PipelineStage.USER_RESPONSE_CREATED.value,
                timer=user_response_timer,
                metadata={
                    "response_kind": user_response.kind.value,
                    "can_continue": user_response.can_continue,
                },
            )

            return AnalysisResult(
                trace_id=trace_id,
                query=query,
                risk_assessment=risk_assessment,
                disposition=AnalysisDisposition.INSUFFICIENT_EVIDENCE,
                completed_stages=completed_stages,
                retrieval_result=retrieval_result,
                grounded_response=None,
                grounding_validation=None,
                user_response=user_response,
                audit=recorder.build(),
            )

        generation_timer = recorder.start_stage()

        try:
            grounded_response = self._response_service.generate(
                query=query,
                retrieval_result=retrieval_result,
            )
        except Exception as error:
            failed_stage = PipelineStage.RESPONSE_GENERATED.value

            recorder.fail_stage(
                stage=failed_stage,
                timer=generation_timer,
                error_type=type(error).__name__,
            )

            raise AnalysisPipelineError(
                trace_id=trace_id,
                failed_stage=failed_stage,
                audit=recorder.build(),
                retryable=True,
            ) from error

        completed_stages.append(PipelineStage.RESPONSE_GENERATED)
        recorder.complete_stage(
            stage=PipelineStage.RESPONSE_GENERATED.value,
            timer=generation_timer,
            metadata={
                "citation_count": len(grounded_response.citations),
            },
        )

        grounding_timer = recorder.start_stage()

        try:
            grounding_validation = self._grounding_validator.validate(
                response=grounded_response,
                retrieval_result=retrieval_result,
            )
        except Exception as error:
            failed_stage = PipelineStage.RESPONSE_VALIDATED.value

            recorder.fail_stage(
                stage=failed_stage,
                timer=grounding_timer,
                error_type=type(error).__name__,
            )

            raise AnalysisPipelineError(
                trace_id=trace_id,
                failed_stage=failed_stage,
                audit=recorder.build(),
                retryable=False,
            ) from error

        completed_stages.append(PipelineStage.RESPONSE_VALIDATED)
        recorder.complete_stage(
            stage=PipelineStage.RESPONSE_VALIDATED.value,
            timer=grounding_timer,
            metadata={
                "is_valid": grounding_validation.is_valid,
                "issue_count": len(grounding_validation.issues),
            },
        )

        if not grounding_validation.is_valid:
            user_response_timer = recorder.start_stage()
            user_response = self._user_response_service.for_rejected_response()

            completed_stages.append(PipelineStage.USER_RESPONSE_CREATED)
            recorder.complete_stage(
                stage=PipelineStage.USER_RESPONSE_CREATED.value,
                timer=user_response_timer,
                metadata={
                    "response_kind": user_response.kind.value,
                    "can_continue": user_response.can_continue,
                },
            )

            return AnalysisResult(
                trace_id=trace_id,
                query=query,
                risk_assessment=risk_assessment,
                disposition=AnalysisDisposition.RESPONSE_REJECTED,
                completed_stages=completed_stages,
                retrieval_result=retrieval_result,
                grounded_response=None,
                grounding_validation=grounding_validation,
                user_response=user_response,
                audit=recorder.build(),
            )

        user_response_timer = recorder.start_stage()
        user_response = self._user_response_service.for_grounded_response(
            grounded_response
        )

        completed_stages.append(PipelineStage.USER_RESPONSE_CREATED)
        recorder.complete_stage(
            stage=PipelineStage.USER_RESPONSE_CREATED.value,
            timer=user_response_timer,
            metadata={
                "response_kind": user_response.kind.value,
                "can_continue": user_response.can_continue,
            },
        )

        return AnalysisResult(
            trace_id=trace_id,
            query=query,
            risk_assessment=risk_assessment,
            disposition=AnalysisDisposition.RESPONSE_GENERATED,
            completed_stages=completed_stages,
            retrieval_result=retrieval_result,
            grounded_response=grounded_response,
            grounding_validation=grounding_validation,
            user_response=user_response,
            audit=recorder.build(),
        )

    def _build_emergency_result(
        self,
        trace_id: UUID,
        query: ClinicalQuery,
        risk_assessment: RiskAssessment,
        completed_stages: list[PipelineStage],
        recorder: PipelineAuditRecorder,
    ) -> AnalysisResult:
        user_response_timer = recorder.start_stage()
        user_response = self._user_response_service.for_emergency()

        completed_stages.append(PipelineStage.USER_RESPONSE_CREATED)
        recorder.complete_stage(
            stage=PipelineStage.USER_RESPONSE_CREATED.value,
            timer=user_response_timer,
            metadata={
                "response_kind": user_response.kind.value,
                "can_continue": user_response.can_continue,
            },
        )

        return AnalysisResult(
            trace_id=trace_id,
            query=query,
            risk_assessment=risk_assessment,
            disposition=AnalysisDisposition.HALTED_EMERGENCY,
            completed_stages=completed_stages,
            retrieval_result=None,
            grounded_response=None,
            grounding_validation=None,
            user_response=user_response,
            audit=recorder.build(),
        )

    def _build_urgent_result(
        self,
        trace_id: UUID,
        query: ClinicalQuery,
        risk_assessment: RiskAssessment,
        completed_stages: list[PipelineStage],
        recorder: PipelineAuditRecorder,
    ) -> AnalysisResult:
        user_response_timer = recorder.start_stage()
        user_response = self._user_response_service.for_urgent()

        completed_stages.append(PipelineStage.USER_RESPONSE_CREATED)
        recorder.complete_stage(
            stage=PipelineStage.USER_RESPONSE_CREATED.value,
            timer=user_response_timer,
            metadata={
                "response_kind": user_response.kind.value,
                "can_continue": user_response.can_continue,
            },
        )

        return AnalysisResult(
            trace_id=trace_id,
            query=query,
            risk_assessment=risk_assessment,
            disposition=AnalysisDisposition.HALTED_URGENT,
            completed_stages=completed_stages,
            retrieval_result=None,
            grounded_response=None,
            grounding_validation=None,
            user_response=user_response,
            audit=recorder.build(),
        )
