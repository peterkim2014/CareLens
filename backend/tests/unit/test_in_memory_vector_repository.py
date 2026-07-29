import pytest

from app.ai.retrieval.semantic import (
    EmbeddingRecord,
    InMemoryVectorRepository,
)


def test_repository_upserts_and_counts_records() -> None:
    repository = InMemoryVectorRepository()

    repository.upsert(
        EmbeddingRecord(
            document_id="allergy-001",
            embedding=[1.0, 0.0],
            embedding_model="hashing",
            content_hash="test-hash",
        )
    )

    assert repository.count() == 1


def test_repository_replaces_existing_record() -> None:
    repository = InMemoryVectorRepository(
        records=[
            EmbeddingRecord(
                document_id="allergy-001",
                embedding=[1.0, 0.0],
                embedding_model="hashing",
                content_hash="test-hash",
            ),
        ]
    )

    repository.upsert(
        EmbeddingRecord(
            document_id="allergy-001",
            embedding=[0.0, 1.0],
            embedding_model="hashing",
            content_hash="test-hash",
        )
    )

    results = repository.search(
        [0.0, 1.0],
        limit=1,
    )

    assert repository.count() == 1
    assert results[0].document_id == "allergy-001"
    assert results[0].similarity == pytest.approx(1.0)


def test_repository_orders_by_cosine_similarity() -> None:
    repository = InMemoryVectorRepository(
        records=[
            EmbeddingRecord(
                document_id="weak",
                embedding=[0.5, 0.5],
                embedding_model="hashing",
                content_hash="test-hash",
            ),
            EmbeddingRecord(
                document_id="strong",
                embedding=[1.0, 0.0],
                embedding_model="hashing",
                content_hash="test-hash",
            ),
        ]
    )

    results = repository.search(
        [1.0, 0.0],
        limit=2,
    )

    assert [result.document_id for result in results] == [
        "strong",
        "weak",
    ]


def test_repository_orders_equal_scores_by_document_id() -> None:
    repository = InMemoryVectorRepository(
        records=[
            EmbeddingRecord(
                document_id="document-b",
                embedding=[1.0, 0.0],
                embedding_model="hashing",
                content_hash="test-hash",
            ),
            EmbeddingRecord(
                document_id="document-a",
                embedding=[1.0, 0.0],
                embedding_model="hashing",
                content_hash="test-hash",
            ),
        ]
    )

    results = repository.search(
        [1.0, 0.0],
        limit=2,
    )

    assert [result.document_id for result in results] == [
        "document-a",
        "document-b",
    ]


def test_repository_applies_limit() -> None:
    repository = InMemoryVectorRepository(
        records=[
            EmbeddingRecord(
                document_id=f"document-{index}",
                embedding=[1.0, 0.0],
                embedding_model="hashing",
                content_hash="test-hash",
            )
            for index in range(5)
        ]
    )

    results = repository.search(
        [1.0, 0.0],
        limit=2,
    )

    assert len(results) == 2


def test_repository_skips_dimension_mismatch() -> None:
    repository = InMemoryVectorRepository(
        records=[
            EmbeddingRecord(
                document_id="different-dimensions",
                embedding=[1.0, 0.0, 0.0],
                embedding_model="hashing",
                content_hash="test-hash",
            ),
        ]
    )

    results = repository.search(
        [1.0, 0.0],
        limit=5,
    )

    assert results == []


def test_repository_deletes_record() -> None:
    repository = InMemoryVectorRepository(
        records=[
            EmbeddingRecord(
                document_id="allergy-001",
                embedding=[1.0, 0.0],
                embedding_model="hashing",
                content_hash="test-hash",
            ),
        ]
    )

    deleted = repository.delete(
        "allergy-001",
    )

    assert deleted is True
    assert repository.count() == 0


def test_repository_returns_false_for_unknown_delete() -> None:
    repository = InMemoryVectorRepository()

    assert repository.delete("missing") is False


def test_repository_clears_records() -> None:
    repository = InMemoryVectorRepository(
        records=[
            EmbeddingRecord(
                document_id="allergy-001",
                embedding=[1.0, 0.0],
                embedding_model="hashing",
                content_hash="test-hash",
            ),
        ]
    )

    repository.clear()

    assert repository.count() == 0


def test_repository_rejects_empty_embedding() -> None:
    repository = InMemoryVectorRepository()

    with pytest.raises(
        ValueError,
        match="embedding cannot be empty",
    ):
        repository.upsert(
            EmbeddingRecord(
                document_id="allergy-001",
                embedding=[],
                embedding_model="hashing",
                content_hash="test-hash",
            )
        )


def test_repository_rejects_invalid_limit() -> None:
    repository = InMemoryVectorRepository()

    with pytest.raises(
        ValueError,
        match="limit",
    ):
        repository.search(
            [1.0],
            limit=0,
        )
