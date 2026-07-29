from enum import StrEnum

from pydantic import BaseModel, Field


class GroundingIssueCode(StrEnum):
    NO_CITATIONS = "no_citations"
    UNKNOWN_DOCUMENT = "unknown_document"
    DUPLICATE_CITATION_ID = "duplicate_citation_id"
    NON_SEQUENTIAL_CITATION_ID = "non_sequential_citation_id"
    MISSING_INLINE_CITATION = "missing_inline_citation"
    UNKNOWN_INLINE_CITATION = "unknown_inline_citation"


class GroundingIssue(BaseModel):
    code: GroundingIssueCode
    message: str
    citation_id: int | None = None
    document_id: str | None = None


class GroundingValidationResult(BaseModel):
    is_valid: bool
    issues: list[GroundingIssue] = Field(default_factory=list)
