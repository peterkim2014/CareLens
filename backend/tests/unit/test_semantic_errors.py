from app.ai.retrieval.semantic import (
    EmbeddingAuthenticationError,
    EmbeddingConfigurationError,
    EmbeddingConnectionError,
    EmbeddingError,
    EmbeddingProviderError,
    EmbeddingRateLimitError,
    EmbeddingResponseError,
    EmbeddingTimeoutError,
)


def test_embedding_errors_share_base_type() -> None:
    error_types = [
        EmbeddingAuthenticationError,
        EmbeddingConfigurationError,
        EmbeddingConnectionError,
        EmbeddingProviderError,
        EmbeddingRateLimitError,
        EmbeddingResponseError,
        EmbeddingTimeoutError,
    ]

    for error_type in error_types:
        assert issubclass(
            error_type,
            EmbeddingError,
        )
