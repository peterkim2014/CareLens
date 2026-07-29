import re

from app.ai.generation import GroundedResponse
from app.ai.retrieval import RetrievalResult
from app.ai.validation.schemas import (
    GroundingIssue,
    GroundingIssueCode,
    GroundingValidationResult,
)

_INLINE_CITATION_PATTERN = re.compile(r"\[(\d+)\]")


class GroundingValidator:
    def validate(
        self,
        response: GroundedResponse,
        retrieval_result: RetrievalResult,
    ) -> GroundingValidationResult:
        issues: list[GroundingIssue] = []

        if not response.citations:
            issues.append(
                GroundingIssue(
                    code=GroundingIssueCode.NO_CITATIONS,
                    message=("A grounded response must contain at least one citation."),
                )
            )

            return GroundingValidationResult(
                is_valid=False,
                issues=issues,
            )

        retrieved_document_ids = {
            evidence.document_id for evidence in retrieval_result.evidence
        }

        citation_ids = [citation.citation_id for citation in response.citations]

        self._validate_unique_citation_ids(
            citation_ids=citation_ids,
            issues=issues,
        )
        self._validate_sequential_citation_ids(
            citation_ids=citation_ids,
            issues=issues,
        )
        self._validate_citation_documents(
            response=response,
            retrieved_document_ids=retrieved_document_ids,
            issues=issues,
        )
        self._validate_inline_citations(
            response=response,
            citation_ids=set(citation_ids),
            issues=issues,
        )

        return GroundingValidationResult(
            is_valid=not issues,
            issues=issues,
        )

    def _validate_unique_citation_ids(
        self,
        citation_ids: list[int],
        issues: list[GroundingIssue],
    ) -> None:
        seen_ids: set[int] = set()

        for citation_id in citation_ids:
            if citation_id in seen_ids:
                issues.append(
                    GroundingIssue(
                        code=(GroundingIssueCode.DUPLICATE_CITATION_ID),
                        message=(f"Citation ID {citation_id} is duplicated."),
                        citation_id=citation_id,
                    )
                )

            seen_ids.add(citation_id)

    def _validate_sequential_citation_ids(
        self,
        citation_ids: list[int],
        issues: list[GroundingIssue],
    ) -> None:
        expected_ids = list(range(1, len(citation_ids) + 1))

        if citation_ids != expected_ids:
            issues.append(
                GroundingIssue(
                    code=(GroundingIssueCode.NON_SEQUENTIAL_CITATION_ID),
                    message=("Citation IDs must begin at 1 and remain sequential."),
                )
            )

    def _validate_citation_documents(
        self,
        response: GroundedResponse,
        retrieved_document_ids: set[str],
        issues: list[GroundingIssue],
    ) -> None:
        for citation in response.citations:
            if citation.document_id not in retrieved_document_ids:
                issues.append(
                    GroundingIssue(
                        code=(GroundingIssueCode.UNKNOWN_DOCUMENT),
                        message=(
                            "Citation references a document that was not retrieved."
                        ),
                        citation_id=citation.citation_id,
                        document_id=citation.document_id,
                    )
                )

    def _validate_inline_citations(
        self,
        response: GroundedResponse,
        citation_ids: set[int],
        issues: list[GroundingIssue],
    ) -> None:
        inline_ids = {
            int(match) for match in _INLINE_CITATION_PATTERN.findall(response.answer)
        }

        for citation_id in sorted(citation_ids - inline_ids):
            issues.append(
                GroundingIssue(
                    code=(GroundingIssueCode.MISSING_INLINE_CITATION),
                    message=(
                        f"Citation [{citation_id}] does not appear "
                        "in the response text."
                    ),
                    citation_id=citation_id,
                )
            )

        for citation_id in sorted(inline_ids - citation_ids):
            issues.append(
                GroundingIssue(
                    code=(GroundingIssueCode.UNKNOWN_INLINE_CITATION),
                    message=(
                        f"Inline citation [{citation_id}] does not "
                        "have a structured citation."
                    ),
                    citation_id=citation_id,
                )
            )
