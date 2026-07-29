from __future__ import annotations

from typing import TYPE_CHECKING

from app.ai.retrieval.semantic.embedder_protocol import (
    Embedder,
)
from app.ai.retrieval.semantic.errors import (
    EmbeddingConfigurationError,
)
from app.ai.retrieval.semantic.hashing_embedder import (
    HashingEmbedder,
)
from app.ai.retrieval.semantic.openai_embedder import (
    OpenAIEmbedder,
)

if TYPE_CHECKING:
    from app.core.config import Settings


def create_embedder(
    settings: Settings,
) -> Embedder:
    if settings.semantic_embedding_provider == "hashing":
        return HashingEmbedder(
            dimensions=(settings.semantic_embedding_dimensions),
        )

    if settings.semantic_embedding_provider == "openai":
        api_key = settings.openai_api_key

        if api_key is None or not api_key.strip():
            raise EmbeddingConfigurationError(
                "OPENAI_API_KEY is required when SEMANTIC_EMBEDDING_PROVIDER=openai.",
            )

        return OpenAIEmbedder(
            api_key=api_key,
            model=settings.openai_embedding_model,
            dimensions=(settings.semantic_embedding_dimensions),
            timeout_seconds=(settings.openai_timeout_seconds),
            maximum_retries=(settings.openai_maximum_retries),
        )

    raise RuntimeError(
        "Unsupported semantic embedding provider: "
        f"{settings.semantic_embedding_provider}.",
    )
