import pytest

from app.ai.retrieval.fusion import (
    reciprocal_rank_fusion,
)


def test_fusion_rewards_documents_in_both_rankings() -> None:
    results = reciprocal_rank_fusion(
        lexical_ranking=[
            "allergy-001",
            "sleep-001",
        ],
        semantic_ranking=[
            "allergy-001",
            "headache-001",
        ],
    )

    assert results[0].document_id == "allergy-001"
    assert results[0].score == pytest.approx(1.0)


def test_fusion_includes_semantic_only_documents() -> None:
    results = reciprocal_rank_fusion(
        lexical_ranking=["allergy-001"],
        semantic_ranking=["headache-001"],
    )

    document_ids = {result.document_id for result in results}

    assert document_ids == {
        "allergy-001",
        "headache-001",
    }


def test_fusion_orders_ties_by_document_id() -> None:
    results = reciprocal_rank_fusion(
        lexical_ranking=[
            "document-b",
            "document-a",
        ],
        semantic_ranking=[
            "document-a",
            "document-b",
        ],
    )

    assert [result.document_id for result in results] == [
        "document-a",
        "document-b",
    ]


def test_fusion_ignores_duplicate_ids_in_ranking() -> None:
    duplicate_results = reciprocal_rank_fusion(
        lexical_ranking=[
            "document-a",
            "document-a",
        ],
        semantic_ranking=[],
    )

    normal_results = reciprocal_rank_fusion(
        lexical_ranking=["document-a"],
        semantic_ranking=[],
    )

    assert duplicate_results == normal_results


def test_fusion_rejects_negative_weight() -> None:
    with pytest.raises(
        ValueError,
        match="lexical_weight",
    ):
        reciprocal_rank_fusion(
            lexical_ranking=[],
            semantic_ranking=[],
            lexical_weight=-1.0,
        )


def test_fusion_requires_positive_weight() -> None:
    with pytest.raises(
        ValueError,
        match="At least one",
    ):
        reciprocal_rank_fusion(
            lexical_ranking=[],
            semantic_ranking=[],
            lexical_weight=0.0,
            semantic_weight=0.0,
        )
