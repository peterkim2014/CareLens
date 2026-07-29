from typing import Annotated

from fastapi import Depends, Request, HTTPException, status

from app.ai.retrieval.repository_protocol import (
    EvidenceRepository,
)
from app.ai.retrieval.semantic.runtime import (
    SemanticRuntime,
)
from app.ai.retrieval.service import RetrievalService
from app.ai.retrieval.sqlalchemy_repository import (
    SQLAlchemyEvidenceRepository,
)
from app.api.dependencies.database import (
    DatabaseSession,
)
from app.core.config import (
    Settings,
    get_settings,
)


def get_evidence_repository(
    session: DatabaseSession,
) -> EvidenceRepository:
    return SQLAlchemyEvidenceRepository(
        session=session,
    )


EvidenceRepositoryDependency = Annotated[
    EvidenceRepository,
    Depends(get_evidence_repository),
]

SettingsDependency = Annotated[
    Settings,
    Depends(get_settings),
]



def get_semantic_runtime(
    request: Request,
) -> SemanticRuntime:
    runtime = request.app.state.semantic_runtime

    if not runtime.is_available:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Semantic retrieval is temporarily unavailable."
            ),
        )

    return runtime


SemanticRuntimeDependency = Annotated[
    SemanticRuntime | None,
    Depends(get_semantic_runtime),
]


def get_retrieval_service(
    repository: EvidenceRepositoryDependency,
    settings: SettingsDependency,
    semantic_runtime: SemanticRuntimeDependency,
) -> RetrievalService:
    semantic_retriever = None

    if settings.semantic_retrieval_enabled and semantic_runtime is not None:
        semantic_retriever = semantic_runtime.retrieval_service

    return RetrievalService(
        repository=repository,
        semantic_retriever=semantic_retriever,
        minimum_score=settings.retrieval_minimum_score,
        maximum_results=(settings.retrieval_maximum_results),
        lexical_weight=(settings.lexical_retrieval_weight),
        semantic_weight=(settings.semantic_retrieval_weight),
    )


RetrievalServiceDependency = Annotated[
    RetrievalService,
    Depends(get_retrieval_service),
]
