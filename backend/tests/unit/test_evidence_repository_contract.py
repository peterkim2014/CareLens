from typing import cast

from app.ai.retrieval.repository import (
    InMemoryEvidenceRepository,
)
from app.ai.retrieval.repository_protocol import (
    EvidenceRepository,
)
from app.ai.retrieval.sqlalchemy_repository import (
    SQLAlchemyEvidenceRepository,
)


def accept_evidence_repository(
    repository: EvidenceRepository,
) -> None:
    del repository


def test_in_memory_repository_satisfies_contract() -> None:
    repository = InMemoryEvidenceRepository(
        documents=[],
    )

    accept_evidence_repository(repository)


def test_sqlalchemy_repository_satisfies_contract() -> None:
    repository = cast(
        SQLAlchemyEvidenceRepository,
        object(),
    )

    accept_evidence_repository(repository)
