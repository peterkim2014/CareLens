from app.ai.generation.schemas import (
    EvidenceCitation,
    GroundedResponse,
)
from app.ai.intake import ClinicalQuery
from app.ai.retrieval import RetrievalResult


class InsufficientEvidenceError(ValueError):
    """Raised when a grounded response cannot be generated."""


class GroundedResponseService:
    def generate(
        self,
        query: ClinicalQuery,
        retrieval_result: RetrievalResult,
    ) -> GroundedResponse:
        if not retrieval_result.evidence:
            raise InsufficientEvidenceError(
                "A grounded response requires at least one evidence item."
            )

        citations: list[EvidenceCitation] = []
        evidence_statements: list[str] = []

        for citation_id, evidence in enumerate(
            retrieval_result.evidence,
            start=1,
        ):
            citations.append(
                EvidenceCitation(
                    citation_id=citation_id,
                    document_id=evidence.document_id,
                    title=evidence.title,
                    source=evidence.source,
                )
            )

            normalized_content = " ".join(evidence.content.split())

            evidence_statements.append(f"{normalized_content} [{citation_id}]")

        answer = self._compose_answer(
            query=query,
            evidence_statements=evidence_statements,
        )

        return GroundedResponse(
            answer=answer,
            citations=citations,
            limitations=[
                (
                    "This response summarizes the available evidence "
                    "and is not a medical diagnosis."
                )
            ],
        )

    def _compose_answer(
        self,
        query: ClinicalQuery,
        evidence_statements: list[str],
    ) -> str:
        evidence_summary = " ".join(evidence_statements)

        return (
            f"For the question: “{query.text}” "
            f"the available evidence indicates: {evidence_summary}"
        )
