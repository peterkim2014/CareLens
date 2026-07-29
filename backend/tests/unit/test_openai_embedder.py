from typing import cast
from unittest.mock import Mock

import pytest
from openai import OpenAI

from app.ai.retrieval.semantic import (
    EmbeddingConfigurationError,
    EmbeddingResponseError,
    OpenAIEmbedder,
)


def create_client(
    *,
    embeddings: list[list[float]],
    indices: list[int] | None = None,
) -> tuple[OpenAI, Mock]:
    if indices is None:
        indices = list(range(len(embeddings)))

    response_data = []

    for embedding, index in zip(
        embeddings,
        indices,
        strict=True,
    ):
        embedding_data = Mock()
        embedding_data.embedding = embedding
        embedding_data.index = index
        response_data.append(
            embedding_data,
        )

    response = Mock()
    response.data = response_data

    create_mock = Mock(
        return_value=response,
    )

    embeddings_resource = Mock()
    embeddings_resource.create = create_mock

    client = Mock()
    client.embeddings = embeddings_resource

    return (
        cast(OpenAI, client),
        create_mock,
    )


def test_openai_embedder_returns_embedding() -> None:
    client, create_mock = create_client(
        embeddings=[
            [
                0.1,
                0.2,
                0.3,
            ],
        ],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        model="text-embedding-3-small",
        dimensions=3,
        client=client,
    )

    result = embedder.embed(
        "seasonal allergies",
    )

    assert result == [
        0.1,
        0.2,
        0.3,
    ]

    create_mock.assert_called_once_with(
        model="text-embedding-3-small",
        input=[
            "seasonal allergies",
        ],
        encoding_format="float",
        dimensions=3,
    )


def test_openai_embedder_embeds_multiple_texts() -> None:
    client, create_mock = create_client(
        embeddings=[
            [
                0.1,
                0.2,
            ],
            [
                0.3,
                0.4,
            ],
        ],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        dimensions=2,
        client=client,
    )

    result = embedder.embed_many(
        [
            "seasonal allergies",
            "sleep hygiene",
        ]
    )

    assert result == [
        [
            0.1,
            0.2,
        ],
        [
            0.3,
            0.4,
        ],
    ]

    create_mock.assert_called_once_with(
        model="text-embedding-3-small",
        input=[
            "seasonal allergies",
            "sleep hygiene",
        ],
        encoding_format="float",
        dimensions=2,
    )


def test_openai_embedder_orders_results_by_index() -> None:
    client, _ = create_client(
        embeddings=[
            [
                0.3,
                0.4,
            ],
            [
                0.1,
                0.2,
            ],
        ],
        indices=[
            1,
            0,
        ],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        client=client,
    )

    result = embedder.embed_many(
        [
            "first",
            "second",
        ]
    )

    assert result == [
        [
            0.1,
            0.2,
        ],
        [
            0.3,
            0.4,
        ],
    ]


def test_openai_embedder_omits_dimensions_when_none() -> None:
    client, create_mock = create_client(
        embeddings=[
            [
                0.1,
                0.2,
            ],
        ],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        client=client,
    )

    embedder.embed(
        "headache symptoms",
    )

    create_mock.assert_called_once_with(
        model="text-embedding-3-small",
        input=[
            "headache symptoms",
        ],
        encoding_format="float",
    )


def test_openai_embedder_returns_empty_for_blank_text() -> None:
    client, create_mock = create_client(
        embeddings=[
            [
                0.1,
            ],
        ],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        client=client,
    )

    assert embedder.embed("   ") == []

    create_mock.assert_not_called()


def test_openai_embedder_returns_empty_for_empty_batch() -> None:
    client, create_mock = create_client(
        embeddings=[],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        client=client,
    )

    assert embedder.embed_many([]) == []

    create_mock.assert_not_called()


def test_openai_embedder_rejects_blank_batch_value() -> None:
    client, create_mock = create_client(
        embeddings=[],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        client=client,
    )

    with pytest.raises(
        ValueError,
        match="blank",
    ):
        embedder.embed_many(
            [
                "valid text",
                " ",
            ]
        )

    create_mock.assert_not_called()


def test_openai_embedder_rejects_unexpected_result_count() -> None:
    client, _ = create_client(
        embeddings=[
            [
                0.1,
                0.2,
            ],
        ],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        client=client,
    )

    with pytest.raises(
        EmbeddingResponseError,
        match="unexpected number",
    ):
        embedder.embed_many(
            [
                "first",
                "second",
            ]
        )


def test_openai_embedder_rejects_blank_api_key() -> None:
    with pytest.raises(
        EmbeddingConfigurationError,
        match="api_key",
    ):
        OpenAIEmbedder(
            api_key=" ",
        )


def test_openai_embedder_rejects_invalid_dimensions() -> None:
    with pytest.raises(
        EmbeddingConfigurationError,
        match="dimensions",
    ):
        OpenAIEmbedder(
            api_key="test-api-key",
            dimensions=0,
        )


def test_openai_embedder_rejects_invalid_timeout() -> None:
    with pytest.raises(
        EmbeddingConfigurationError,
        match="timeout_seconds",
    ):
        OpenAIEmbedder(
            api_key="test-api-key",
            timeout_seconds=0,
        )


def test_openai_embedder_rejects_negative_retries() -> None:
    with pytest.raises(
        EmbeddingConfigurationError,
        match="maximum_retries",
    ):
        OpenAIEmbedder(
            api_key="test-api-key",
            maximum_retries=-1,
        )


def test_openai_embedder_rejects_invalid_indices() -> None:
    client, _ = create_client(
        embeddings=[
            [
                0.1,
                0.2,
            ],
            [
                0.3,
                0.4,
            ],
        ],
        indices=[
            0,
            2,
        ],
    )

    embedder = OpenAIEmbedder(
        api_key="test-api-key",
        client=client,
    )

    with pytest.raises(
        EmbeddingResponseError,
        match="indices",
    ):
        embedder.embed_many(
            [
                "first",
                "second",
            ]
        )
