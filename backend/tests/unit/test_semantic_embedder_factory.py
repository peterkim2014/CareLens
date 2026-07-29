import pytest

from app.ai.retrieval.semantic import (
    EmbeddingConfigurationError,
    HashingEmbedder,
    OpenAIEmbedder,
    create_embedder,
)
from app.core.config import Settings


def test_factory_creates_hashing_embedder() -> None:
    settings = Settings(
        semantic_embedding_provider="hashing",
        semantic_embedding_dimensions=32,
    )

    embedder = create_embedder(
        settings,
    )

    assert isinstance(
        embedder,
        HashingEmbedder,
    )
    assert embedder.dimensions == 32


def test_factory_creates_openai_embedder() -> None:
    settings = Settings(
        semantic_embedding_provider="openai",
        semantic_embedding_dimensions=256,
        openai_api_key="test-api-key",
        openai_embedding_model=("text-embedding-3-small"),
        openai_timeout_seconds=15.0,
        openai_maximum_retries=3,
    )

    embedder = create_embedder(
        settings,
    )

    assert isinstance(
        embedder,
        OpenAIEmbedder,
    )
    assert embedder.dimensions == 256
    assert embedder.model == "text-embedding-3-small"


def test_factory_requires_openai_api_key() -> None:
    settings = Settings(
        semantic_embedding_provider="openai",
        openai_api_key=None,
    )

    with pytest.raises(
        EmbeddingConfigurationError,
        match="OPENAI_API_KEY",
    ):
        create_embedder(
            settings,
        )
