from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RankedDocument:
    document_id: str
    score: float


def reciprocal_rank_fusion(
    *,
    lexical_ranking: Sequence[str],
    semantic_ranking: Sequence[str],
    lexical_weight: float = 1.0,
    semantic_weight: float = 1.0,
    rank_constant: int = 60,
) -> list[RankedDocument]:
    if lexical_weight < 0.0:
        raise ValueError(
            "lexical_weight cannot be negative.",
        )

    if semantic_weight < 0.0:
        raise ValueError(
            "semantic_weight cannot be negative.",
        )

    if lexical_weight == 0.0 and semantic_weight == 0.0:
        raise ValueError(
            "At least one ranking weight must be positive.",
        )

    if rank_constant < 1:
        raise ValueError(
            "rank_constant must be at least 1.",
        )

    fused_scores: dict[str, float] = {}

    _add_ranking_scores(
        fused_scores=fused_scores,
        ranking=lexical_ranking,
        weight=lexical_weight,
        rank_constant=rank_constant,
    )
    _add_ranking_scores(
        fused_scores=fused_scores,
        ranking=semantic_ranking,
        weight=semantic_weight,
        rank_constant=rank_constant,
    )

    maximum_possible_score = (lexical_weight + semantic_weight) / (rank_constant + 1)

    results = [
        RankedDocument(
            document_id=document_id,
            score=min(
                score / maximum_possible_score,
                1.0,
            ),
        )
        for document_id, score in fused_scores.items()
    ]

    results.sort(
        key=lambda result: (
            -result.score,
            result.document_id,
        ),
    )

    return results


def _add_ranking_scores(
    *,
    fused_scores: dict[str, float],
    ranking: Sequence[str],
    weight: float,
    rank_constant: int,
) -> None:
    if weight == 0.0:
        return

    seen_document_ids: set[str] = set()

    for rank, document_id in enumerate(
        ranking,
        start=1,
    ):
        if document_id in seen_document_ids:
            continue

        seen_document_ids.add(document_id)

        contribution = weight / (rank_constant + rank)

        fused_scores[document_id] = fused_scores.get(document_id, 0.0) + contribution
