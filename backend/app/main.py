import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import (
    FastAPI,
    Request,
    status,
)
from fastapi.exceptions import (
    RequestValidationError,
)
from fastapi.responses import JSONResponse

from app.ai.retrieval.semantic.errors import (
    EmbeddingError,
)
from app.ai.retrieval.semantic.factory import (
    create_embedder,
)
from app.ai.retrieval.semantic.runtime import (
    build_semantic_runtime,
)
from app.ai.retrieval.semantic.sqlalchemy_repository import (
    SQLAlchemyVectorRepository,
)
from app.ai.retrieval.sqlalchemy_repository import (
    SQLAlchemyEvidenceRepository,
)
from app.api.routes import api_router
from app.core.config import get_settings
from app.core.errors import (
    AnalysisPipelineError,
    handle_analysis_pipeline_error,
)
from app.core.telemetry import (
    TraceCorrelationMiddleware,
    configure_logging,
    get_trace_id,
)
from app.db.session import SessionFactory

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(
    application: FastAPI,
) -> AsyncIterator[None]:
    settings = get_settings()

    application.state.semantic_runtime = None

    logger.info(
        "Application started",
        extra={
            "event": "application_started",
            "semantic_retrieval_enabled": (settings.semantic_retrieval_enabled),
        },
    )

    try:
        if settings.semantic_retrieval_enabled:
            with SessionFactory() as session:
                evidence_repository = SQLAlchemyEvidenceRepository(
                    session=session,
                )

                vector_repository = SQLAlchemyVectorRepository(
                    session_factory=SessionFactory,
                )

                try:
                    embedder = create_embedder(
                        settings,
                    )

                    semantic_runtime = build_semantic_runtime(
                        evidence_repository,
                        embedder=embedder,
                        vector_repository=(vector_repository),
                        batch_size=(settings.semantic_embedding_batch_size),
                    )
                except EmbeddingError:
                    logger.exception(
                        "Semantic retrieval startup failed",
                        extra={
                            "event": ("semantic_index_startup_failed"),
                            "embedding_provider": (
                                settings.semantic_embedding_provider
                            ),
                            "embedding_model": (settings.openai_embedding_model),
                        },
                    )
                    raise

                application.state.semantic_runtime = semantic_runtime

                indexing_result = semantic_runtime.indexing_result

                logger.info(
                    "Semantic retrieval index built",
                    extra={
                        "event": "semantic_index_built",
                        "total_documents": (indexing_result.total_documents),
                        "indexed_documents": (indexing_result.indexed_documents),
                        "skipped_documents": (indexing_result.skipped_documents),
                        "embedding_provider": (settings.semantic_embedding_provider),
                        "embedding_model": (
                            settings.openai_embedding_model
                            if (settings.semantic_embedding_provider == "openai")
                            else "hashing"
                        ),
                        "embedding_dimensions": (
                            settings.semantic_embedding_dimensions
                        ),
                        "embedding_batch_size": (
                            settings.semantic_embedding_batch_size
                        ),
                    },
                )

        yield
    finally:
        application.state.semantic_runtime = None

        logger.info(
            "Application stopped",
            extra={
                "event": "application_stopped",
            },
        )


def create_app() -> FastAPI:
    settings = get_settings()

    configure_logging(
        debug=settings.debug,
    )

    application = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
        docs_url=("/docs" if settings.environment != "production" else None),
        redoc_url=("/redoc" if settings.environment != "production" else None),
        openapi_url=("/openapi.json" if settings.environment != "production" else None),
    )

    application.add_middleware(
        TraceCorrelationMiddleware,
    )

    application.include_router(
        api_router,
        prefix=settings.api_prefix,
    )

    register_exception_handlers(
        application,
    )

    return application


def register_exception_handlers(
    application: FastAPI,
) -> None:
    application.add_exception_handler(
        AnalysisPipelineError,
        handle_analysis_pipeline_error,
    )

    @application.exception_handler(
        RequestValidationError,
    )
    async def validation_exception_handler(
        _: Request,
        exception: RequestValidationError,
    ) -> JSONResponse:
        trace_id = get_trace_id()

        logger.warning(
            "Request validation failed",
            extra={
                "event": "request_validation_failed",
                "error_count": len(
                    exception.errors(),
                ),
            },
        )

        error: dict[str, Any] = {
            "code": "validation_error",
            "message": ("The request contains invalid data."),
            "details": exception.errors(),
        }

        if trace_id is not None:
            error["trace_id"] = str(
                trace_id,
            )

        return JSONResponse(
            status_code=(status.HTTP_422_UNPROCESSABLE_CONTENT),
            content={
                "error": error,
            },
        )

    @application.exception_handler(Exception)
    async def unexpected_exception_handler(
        _: Request,
        exception: Exception,
    ) -> JSONResponse:
        settings = get_settings()
        trace_id = get_trace_id()

        logger.error(
            "Unexpected application error",
            extra={
                "event": ("unexpected_application_error"),
                "error_type": type(
                    exception,
                ).__name__,
            },
        )

        error: dict[str, Any] = {
            "code": "internal_server_error",
            "message": ("An unexpected error occurred."),
        }

        if trace_id is not None:
            error["trace_id"] = str(
                trace_id,
            )

        if settings.debug:
            error["details"] = type(
                exception,
            ).__name__

        return JSONResponse(
            status_code=(status.HTTP_500_INTERNAL_SERVER_ERROR),
            content={
                "error": error,
            },
        )


app = create_app()
