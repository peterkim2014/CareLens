class EmbeddingError(RuntimeError):
    """Base exception for embedding failures."""


class EmbeddingConfigurationError(
    EmbeddingError,
):
    """Raised when an embedding provider is misconfigured."""


class EmbeddingAuthenticationError(
    EmbeddingError,
):
    """Raised when provider authentication fails."""


class EmbeddingRateLimitError(
    EmbeddingError,
):
    """Raised when the provider rate limit is exceeded."""


class EmbeddingTimeoutError(
    EmbeddingError,
):
    """Raised when an embedding request times out."""


class EmbeddingConnectionError(
    EmbeddingError,
):
    """Raised when the provider cannot be reached."""


class EmbeddingProviderError(
    EmbeddingError,
):
    """Raised for other provider-side failures."""


class EmbeddingResponseError(
    EmbeddingError,
):
    """Raised when a provider returns an invalid response."""
