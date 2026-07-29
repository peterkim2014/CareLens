from typing import Annotated

from fastapi import Depends
from starlette.requests import Request

from app.ai.retrieval import (
    EvidenceRepository,
    RetrievalService,
)
from app.ai.retrieval.semantic import (
    SemanticRuntime,
)
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
) -> SemanticRuntime | None:
    runtime: SemanticRuntime | None = getattr(
        request.app.state,
        "semantic_runtime",
        None,
    )

    return runtime


SemanticRuntimeDependency = Annotated[
    SemanticRuntime | None,
    Depends(get_semantic_runtime),
]


def recover_semantic_runtime(
    semantic_runtime: SemanticRuntimeDependency,
    settings: SettingsDependency,
) -> SemanticRuntime | None:
    if (
        not settings.semantic_retrieval_enabled
        or semantic_runtime is None
        or semantic_runtime.is_available
    ):
        return semantic_runtime

    semantic_runtime.attempt_recovery()

    return semantic_runtime


RecoveredSemanticRuntimeDependency = Annotated[
    SemanticRuntime | None,
    Depends(recover_semantic_runtime),
]


def get_retrieval_service(
    repository: EvidenceRepositoryDependency,
    settings: SettingsDependency,
    semantic_runtime: RecoveredSemanticRuntimeDependency,
) -> RetrievalService:
    semantic_retriever = None
    semantic_failure_handler = None

    if (
        settings.semantic_retrieval_enabled
        and semantic_runtime is not None
        and semantic_runtime.is_available
    ):
        semantic_retriever = semantic_runtime.retrieval_service
        semantic_failure_handler = semantic_runtime.mark_unavailable

    return RetrievalService(
        repository=repository,
        semantic_retriever=semantic_retriever,
        semantic_failure_handler=(semantic_failure_handler),
        minimum_score=(settings.retrieval_minimum_score),
        maximum_results=(settings.retrieval_maximum_results),
        lexical_weight=(settings.lexical_retrieval_weight),
        semantic_weight=(settings.semantic_retrieval_weight),
    )


RetrievalServiceDependency = Annotated[
    RetrievalService,
    Depends(get_retrieval_service),
]
