import math

import pytest

from app.ai.retrieval.semantic import (
    HashingEmbedder,
)


def test_hashing_embedder_is_deterministic() -> None:
    embedder = HashingEmbedder(
        dimensions=32,
    )

    first = embedder.embed(
        "seasonal allergies",
    )
    second = embedder.embed(
        "seasonal allergies",
    )

    assert first == second


def test_hashing_embedder_returns_configured_dimensions() -> None:
    embedder = HashingEmbedder(
        dimensions=24,
    )

    embedding = embedder.embed(
        "headache symptoms",
    )

    assert len(embedding) == 24


def test_hashing_embedder_normalizes_embedding() -> None:
    embedder = HashingEmbedder(
        dimensions=32,
    )

    embedding = embedder.embed(
        "seasonal allergies",
    )

    magnitude = math.sqrt(sum(value * value for value in embedding))

    assert magnitude == pytest.approx(1.0)


def test_hashing_embedder_returns_empty_for_blank_text() -> None:
    embedder = HashingEmbedder()

    assert embedder.embed("   ") == []


def test_hashing_embedder_rejects_invalid_dimensions() -> None:
    with pytest.raises(
        ValueError,
        match="dimensions",
    ):
        HashingEmbedder(
            dimensions=0,
        )
