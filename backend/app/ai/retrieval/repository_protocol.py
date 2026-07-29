from typing import Protocol

from app.ai.retrieval.schemas import EvidenceDocument


class EvidenceRepository(Protocol):
    def list_documents(
        self,
    ) -> list[EvidenceDocument]: ...
