from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    OpenAI,
    RateLimitError,
)
from openai.types import CreateEmbeddingResponse

from app.ai.retrieval.semantic.errors import (
    EmbeddingAuthenticationError,
    EmbeddingConfigurationError,
    EmbeddingConnectionError,
    EmbeddingProviderError,
    EmbeddingRateLimitError,
    EmbeddingResponseError,
    EmbeddingTimeoutError,
)


class OpenAIEmbedder:
    def __init__(
        self,
        *,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int | None = None,
        timeout_seconds: float = 30.0,
        maximum_retries: int = 2,
        client: OpenAI | None = None,
    ) -> None:
        normalized_api_key = api_key.strip()
        normalized_model = model.strip()

        if not normalized_api_key:
            raise EmbeddingConfigurationError(
                "api_key cannot be blank.",
            )

        if not normalized_model:
            raise EmbeddingConfigurationError(
                "model cannot be blank.",
            )

        if dimensions is not None and dimensions < 1:
            raise EmbeddingConfigurationError(
                "dimensions must be at least 1.",
            )

        if timeout_seconds <= 0:
            raise EmbeddingConfigurationError(
                "timeout_seconds must be greater than zero.",
            )

        if maximum_retries < 0:
            raise EmbeddingConfigurationError(
                "maximum_retries cannot be negative.",
            )

        self._model = normalized_model
        self._dimensions = dimensions

        self._client = client or OpenAI(
            api_key=normalized_api_key,
            timeout=timeout_seconds,
            max_retries=maximum_retries,
        )

    @property
    def model(self) -> str:
        return self._model

    @property
    def dimensions(self) -> int | None:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model

    def embed(
        self,
        text: str,
    ) -> list[float]:
        normalized_text = text.strip()

        if not normalized_text:
            return []

        embeddings = self.embed_many(
            [
                normalized_text,
            ]
        )

        if not embeddings:
            raise EmbeddingResponseError(
                "OpenAI returned no embeddings.",
            )

        return embeddings[0]

    def embed_many(
        self,
        texts: list[str],
    ) -> list[list[float]]:
        if not texts:
            return []

        normalized_texts = [text.strip() for text in texts]

        if any(not text for text in normalized_texts):
            raise ValueError(
                "texts cannot contain blank values.",
            )

        try:
            response = self._create_embeddings(
                normalized_texts,
            )
        except AuthenticationError as error:
            raise EmbeddingAuthenticationError(
                "OpenAI authentication failed.",
            ) from error
        except RateLimitError as error:
            raise EmbeddingRateLimitError(
                "OpenAI embedding rate limit was exceeded.",
            ) from error
        except APITimeoutError as error:
            raise EmbeddingTimeoutError(
                "OpenAI embedding request timed out.",
            ) from error
        except APIConnectionError as error:
            raise EmbeddingConnectionError(
                "Could not connect to OpenAI.",
            ) from error
        except BadRequestError as error:
            raise EmbeddingProviderError(
                "OpenAI rejected the embedding request.",
            ) from error
        except APIError as error:
            raise EmbeddingProviderError(
                "OpenAI embedding request failed.",
            ) from error

        if not response.data:
            raise EmbeddingResponseError(
                "OpenAI returned no embedding data.",
            )

        ordered_data = sorted(
            response.data,
            key=lambda item: item.index,
        )

        if len(ordered_data) != len(normalized_texts):
            raise EmbeddingResponseError(
                "OpenAI returned an unexpected number of embeddings.",
            )

        expected_indices = list(range(len(normalized_texts)))
        actual_indices = [item.index for item in ordered_data]

        if actual_indices != expected_indices:
            raise EmbeddingResponseError(
                "OpenAI returned invalid embedding indices.",
            )

        embeddings = [list(item.embedding) for item in ordered_data]

        if any(not embedding for embedding in embeddings):
            raise EmbeddingResponseError(
                "OpenAI returned an empty embedding.",
            )

        return embeddings

    def _create_embeddings(
        self,
        texts: list[str],
    ) -> CreateEmbeddingResponse:
        if self._dimensions is None:
            return self._client.embeddings.create(
                model=self._model,
                input=texts,
                encoding_format="float",
            )

        return self._client.embeddings.create(
            model=self._model,
            input=texts,
            encoding_format="float",
            dimensions=self._dimensions,
        )
