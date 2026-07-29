from app.ai.generation import (
    EvidenceCitation,
    GroundedResponse,
    GroundedResponseService,
)
from app.ai.intake import ClinicalQuery, RiskClassifier
from app.ai.pipeline import (
    AnalysisDisposition,
    AnalysisPipeline,
    AnalysisResult,
    PipelineStage,
)
from app.ai.responses import (
    UserResponseKind,
    UserResponseService,
)
from app.ai.retrieval import (
    EvidenceDocument,
    InMemoryEvidenceRepository,
    RetrievalResult,
    RetrievalService,
)
from app.ai.validation import GroundingValidator
from app.core.errors import AnalysisPipelineError


def create_pipeline(
    response_service: GroundedResponseService | None = None,
    retrieval_service: RetrievalService | None = None,
) -> AnalysisPipeline:
    repository = InMemoryEvidenceRepository(
        documents=[
            EvidenceDocument(
                document_id="allergy-001",
                title="Seasonal allergy symptoms",
                content=("Seasonal allergies commonly cause sneezing and itchy eyes."),
                source="Clinical Reference",
                source_type="clinical_reference",
            )
        ]
    )

    default_retrieval_service = RetrievalService(repository)

    return AnalysisPipeline(
        risk_classifier=RiskClassifier(),
        retrieval_service=(retrieval_service or default_retrieval_service),
        response_service=(response_service or GroundedResponseService()),
        grounding_validator=GroundingValidator(),
        user_response_service=UserResponseService(),
    )


class FailingRetrievalService(RetrievalService):
    def retrieve(self, query: str) -> RetrievalResult:
        del query
        raise RuntimeError("Private retrieval failure details")


class FailingGroundedResponseService(GroundedResponseService):
    def generate(
        self,
        query: ClinicalQuery,
        retrieval_result: RetrievalResult,
    ) -> GroundedResponse:
        del query
        del retrieval_result
        raise RuntimeError("Private generation failure details")


def test_pipeline_wraps_retrieval_failure() -> None:
    repository = InMemoryEvidenceRepository(documents=[])

    pipeline = create_pipeline(retrieval_service=FailingRetrievalService(repository))

    query = ClinicalQuery(text="What symptoms do seasonal allergies cause?")

    try:
        pipeline.run(query)
    except AnalysisPipelineError as error:
        assert error.failed_stage == PipelineStage.EVIDENCE_RETRIEVED.value
        assert error.retryable is True

        failed_event = error.audit.events[-1]

        assert failed_event.stage == PipelineStage.EVIDENCE_RETRIEVED.value
        assert failed_event.status.value == "failed"
        assert failed_event.metadata["error_type"] == "RuntimeError"
        assert query.text not in error.audit.model_dump_json()
    else:
        raise AssertionError("Expected AnalysisPipelineError")


def test_pipeline_wraps_generation_failure() -> None:
    pipeline = create_pipeline(response_service=FailingGroundedResponseService())

    query = ClinicalQuery(text="What symptoms do seasonal allergies cause?")

    try:
        pipeline.run(query)
    except AnalysisPipelineError as error:
        assert error.failed_stage == PipelineStage.RESPONSE_GENERATED.value
        assert error.retryable is True

        failed_event = error.audit.events[-1]

        assert failed_event.stage == PipelineStage.RESPONSE_GENERATED.value
        assert failed_event.status.value == "failed"
        assert failed_event.metadata["error_type"] == "RuntimeError"
        assert query.text not in error.audit.model_dump_json()
    else:
        raise AssertionError("Expected AnalysisPipelineError")


def assert_audit_matches_completed_stages(
    result: AnalysisResult,
) -> None:
    completed_stages = [stage.value for stage in result.completed_stages]

    audited_stages = [event.stage for event in result.audit.events]

    assert audited_stages == completed_stages
    assert result.audit.total_duration_ms >= 0
    assert result.audit.completed_at >= result.audit.started_at

    for event in result.audit.events:
        assert event.duration_ms >= 0
        assert event.completed_at >= event.started_at
        assert event.status.value == "completed"


class InvalidGroundedResponseService(GroundedResponseService):
    def generate(
        self,
        query: ClinicalQuery,
        retrieval_result: RetrievalResult,
    ) -> GroundedResponse:
        del query
        del retrieval_result

        return GroundedResponse(
            answer="This answer cites invented evidence. [1]",
            citations=[
                EvidenceCitation(
                    citation_id=1,
                    document_id="invented-document",
                    title="Invented evidence",
                    source="Unknown",
                )
            ],
            limitations=[],
        )


def test_emergency_query_halts_pipeline() -> None:
    pipeline = create_pipeline()

    result = pipeline.run(ClinicalQuery(text="I have severe chest pain."))

    assert result.disposition is AnalysisDisposition.HALTED_EMERGENCY
    assert result.retrieval_result is None
    assert result.grounded_response is None
    assert result.grounding_validation is None
    assert result.user_response.kind is UserResponseKind.EMERGENCY
    assert result.user_response.can_continue is False
    assert result.completed_stages == [
        PipelineStage.INTAKE_VALIDATED,
        PipelineStage.RISK_ASSESSED,
        PipelineStage.SAFETY_ROUTED,
        PipelineStage.USER_RESPONSE_CREATED,
    ]

    assert_audit_matches_completed_stages(result)


def test_urgent_query_halts_pipeline() -> None:
    pipeline = create_pipeline()

    result = pipeline.run(ClinicalQuery(text="I cannot keep water down."))

    assert result.disposition is AnalysisDisposition.HALTED_URGENT
    assert result.retrieval_result is None
    assert result.grounded_response is None
    assert result.grounding_validation is None
    assert result.user_response.kind is UserResponseKind.URGENT
    assert result.user_response.can_continue is False
    assert result.completed_stages == [
        PipelineStage.INTAKE_VALIDATED,
        PipelineStage.RISK_ASSESSED,
        PipelineStage.SAFETY_ROUTED,
        PipelineStage.USER_RESPONSE_CREATED,
    ]

    assert_audit_matches_completed_stages(result)


def test_routine_query_generates_validated_response() -> None:
    pipeline = create_pipeline()

    result = pipeline.run(
        ClinicalQuery(text=("What symptoms do seasonal allergies cause?"))
    )

    assert result.disposition is AnalysisDisposition.RESPONSE_GENERATED
    assert result.retrieval_result is not None
    assert result.grounded_response is not None
    assert result.grounding_validation is not None
    assert result.grounding_validation.is_valid is True
    assert result.grounding_validation.issues == []
    assert result.user_response.kind is UserResponseKind.GROUNDED
    assert result.user_response.can_continue is True
    assert result.user_response.message == result.grounded_response.answer
    assert result.completed_stages == [
        PipelineStage.INTAKE_VALIDATED,
        PipelineStage.RISK_ASSESSED,
        PipelineStage.SAFETY_ROUTED,
        PipelineStage.EVIDENCE_RETRIEVED,
        PipelineStage.EVIDENCE_VALIDATED,
        PipelineStage.RESPONSE_GENERATED,
        PipelineStage.RESPONSE_VALIDATED,
        PipelineStage.USER_RESPONSE_CREATED,
    ]

    assert_audit_matches_completed_stages(result)


def test_pipeline_stops_when_evidence_is_insufficient() -> None:
    pipeline = create_pipeline()

    result = pipeline.run(ClinicalQuery(text="What causes kidney stones?"))

    assert result.disposition is AnalysisDisposition.INSUFFICIENT_EVIDENCE
    assert result.retrieval_result is not None
    assert result.retrieval_result.evidence == []
    assert result.grounded_response is None
    assert result.grounding_validation is None
    assert result.user_response.kind is UserResponseKind.INSUFFICIENT_EVIDENCE
    assert result.user_response.can_continue is True
    assert result.completed_stages == [
        PipelineStage.INTAKE_VALIDATED,
        PipelineStage.RISK_ASSESSED,
        PipelineStage.SAFETY_ROUTED,
        PipelineStage.EVIDENCE_RETRIEVED,
        PipelineStage.EVIDENCE_VALIDATED,
        PipelineStage.USER_RESPONSE_CREATED,
    ]

    assert_audit_matches_completed_stages(result)


def test_pipeline_rejects_ungrounded_response() -> None:
    pipeline = create_pipeline(response_service=InvalidGroundedResponseService())

    result = pipeline.run(
        ClinicalQuery(text=("What symptoms do seasonal allergies cause?"))
    )

    assert result.disposition is AnalysisDisposition.RESPONSE_REJECTED
    assert result.retrieval_result is not None
    assert result.grounded_response is None
    assert result.grounding_validation is not None
    assert result.grounding_validation.is_valid is False
    assert result.grounding_validation.issues
    assert result.user_response.kind is UserResponseKind.RESPONSE_REJECTED
    assert result.user_response.can_continue is True
    assert result.completed_stages == [
        PipelineStage.INTAKE_VALIDATED,
        PipelineStage.RISK_ASSESSED,
        PipelineStage.SAFETY_ROUTED,
        PipelineStage.EVIDENCE_RETRIEVED,
        PipelineStage.EVIDENCE_VALIDATED,
        PipelineStage.RESPONSE_GENERATED,
        PipelineStage.RESPONSE_VALIDATED,
        PipelineStage.USER_RESPONSE_CREATED,
    ]

    assert_audit_matches_completed_stages(result)


def test_each_pipeline_run_receives_unique_trace_id() -> None:
    pipeline = create_pipeline()

    query = ClinicalQuery(text="What symptoms do seasonal allergies cause?")

    first_result = pipeline.run(query)
    second_result = pipeline.run(query)

    assert first_result.trace_id != second_result.trace_id

    assert_audit_matches_completed_stages(first_result)
    assert_audit_matches_completed_stages(second_result)


def test_audit_contains_risk_metadata() -> None:
    pipeline = create_pipeline()

    result = pipeline.run(
        ClinicalQuery(text=("What symptoms do seasonal allergies cause?"))
    )

    risk_event = next(
        event
        for event in result.audit.events
        if event.stage == PipelineStage.RISK_ASSESSED.value
    )

    assert risk_event.metadata["risk_level"] == "routine"
    assert risk_event.metadata["signal_count"] == 0


def test_audit_contains_retrieval_metadata() -> None:
    pipeline = create_pipeline()

    result = pipeline.run(
        ClinicalQuery(text=("What symptoms do seasonal allergies cause?"))
    )

    retrieval_event = next(
        event
        for event in result.audit.events
        if (event.stage == PipelineStage.EVIDENCE_RETRIEVED.value)
    )

    assert retrieval_event.metadata["evidence_count"] == 1
    assert retrieval_event.metadata["total_candidates"] == 1


def test_audit_contains_grounding_metadata() -> None:
    pipeline = create_pipeline()

    result = pipeline.run(
        ClinicalQuery(text=("What symptoms do seasonal allergies cause?"))
    )

    validation_event = next(
        event
        for event in result.audit.events
        if (event.stage == PipelineStage.RESPONSE_VALIDATED.value)
    )

    assert validation_event.metadata["is_valid"] is True
    assert validation_event.metadata["issue_count"] == 0


def test_audit_does_not_store_query_text() -> None:
    pipeline = create_pipeline()

    query = ClinicalQuery(
        text=("My private symptom description should not appear in audit metadata.")
    )

    result = pipeline.run(query)

    serialized_audit = result.audit.model_dump_json()

    assert query.text not in serialized_audit
