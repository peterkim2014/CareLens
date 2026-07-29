from app.ai.retrieval.repository_protocol import (
    EvidenceRepository,
)
from app.ai.retrieval.schemas import EvidenceDocument


class InMemoryEvidenceRepository:
    def __init__(
        self,
        documents: list[EvidenceDocument],
    ) -> None:
        self._documents = list(documents)

    def list_documents(self) -> list[EvidenceDocument]:
        return list(self._documents)


def _verify_repository_contract(
    repository: InMemoryEvidenceRepository,
) -> EvidenceRepository:
    return repository
