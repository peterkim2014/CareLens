from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.ai.retrieval import SQLAlchemyEvidenceRepository
from app.api.dependencies.retrieval import (
    get_evidence_repository,
)


def test_repository_dependency_uses_request_session() -> None:
    session = MagicMock(spec=Session)

    repository = get_evidence_repository(
        session=session,
    )

    assert isinstance(
        repository,
        SQLAlchemyEvidenceRepository,
    )
