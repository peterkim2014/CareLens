from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)

from app.core.constants import (
    SEMANTIC_EMBEDDING_DIMENSIONS,
)


class Settings(BaseSettings):
    app_name: str = "CareLens API"
    app_version: str = "0.1.0"

    environment: Literal[
        "development",
        "test",
        "staging",
        "production",
    ] = "development"

    debug: bool = False
    api_prefix: str = "/api/v1"

    database_url: str = "postgresql+psycopg://pmia@localhost:5432/carelens"

    retrieval_minimum_score: float = Field(
        default=0.1,
        ge=0.0,
    )
    retrieval_maximum_results: int = Field(
        default=5,
        ge=1,
    )

    semantic_retrieval_enabled: bool = False

    semantic_embedding_provider: Literal[
        "hashing",
        "openai",
    ] = "hashing"

    semantic_embedding_dimensions: int = Field(
        default=SEMANTIC_EMBEDDING_DIMENSIONS,
        ge=1,
    )

    semantic_embedding_batch_size: int = Field(
        default=100,
        ge=1,
        le=2048,
    )

    openai_api_key: str | None = None
    openai_embedding_model: str = "text-embedding-3-small"

    openai_timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
    )

    openai_maximum_retries: int = Field(
        default=2,
        ge=0,
        le=10,
    )

    lexical_retrieval_weight: float = Field(
        default=1.0,
        ge=0.0,
    )
    semantic_retrieval_weight: float = Field(
        default=1.0,
        ge=0.0,
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
