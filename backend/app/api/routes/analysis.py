from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.ai.generation import GroundedResponseService
from app.ai.intake import (
    ClinicalQuery,
    RiskAssessment,
    RiskClassifier,
)
from app.ai.pipeline import AnalysisPipeline, AnalysisResult
from app.ai.responses import UserResponseService
from app.ai.validation import GroundingValidator
from app.api.dependencies.retrieval import (
    RetrievalServiceDependency,
)
from app.core.errors import APIErrorResponse

router = APIRouter(
    prefix="/analysis",
    tags=["Analysis"],
)


def get_risk_classifier() -> RiskClassifier:
    return RiskClassifier()


RiskClassifierDependency = Annotated[
    RiskClassifier,
    Depends(get_risk_classifier),
]


def get_grounded_response_service() -> GroundedResponseService:
    return GroundedResponseService()


GroundedResponseServiceDependency = Annotated[
    GroundedResponseService,
    Depends(get_grounded_response_service),
]


def get_grounding_validator() -> GroundingValidator:
    return GroundingValidator()


GroundingValidatorDependency = Annotated[
    GroundingValidator,
    Depends(get_grounding_validator),
]


def get_user_response_service() -> UserResponseService:
    return UserResponseService()


UserResponseServiceDependency = Annotated[
    UserResponseService,
    Depends(get_user_response_service),
]


def get_analysis_pipeline(
    classifier: RiskClassifierDependency,
    retrieval_service: RetrievalServiceDependency,
    response_service: GroundedResponseServiceDependency,
    grounding_validator: GroundingValidatorDependency,
    user_response_service: UserResponseServiceDependency,
) -> AnalysisPipeline:
    return AnalysisPipeline(
        risk_classifier=classifier,
        retrieval_service=retrieval_service,
        response_service=response_service,
        grounding_validator=grounding_validator,
        user_response_service=user_response_service,
    )


AnalysisPipelineDependency = Annotated[
    AnalysisPipeline,
    Depends(get_analysis_pipeline),
]


@router.post(
    "/risk",
    response_model=RiskAssessment,
    status_code=status.HTTP_200_OK,
)
def assess_risk(
    query: ClinicalQuery,
    classifier: RiskClassifierDependency,
) -> RiskAssessment:
    return classifier.classify(query)


@router.post(
    "",
    response_model=AnalysisResult,
    status_code=status.HTTP_200_OK,
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": APIErrorResponse,
            "description": (
                "The analysis pipeline failed before a safe response could be produced."
            ),
        }
    },
)
def analyze_query(
    query: ClinicalQuery,
    pipeline: AnalysisPipelineDependency,
) -> AnalysisResult:
    return pipeline.run(query)
