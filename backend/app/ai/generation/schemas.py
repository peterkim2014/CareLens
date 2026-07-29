from pydantic import BaseModel, Field


class EvidenceCitation(BaseModel):
    citation_id: int = Field(ge=1)
    document_id: str
    title: str
    source: str


class GroundedResponse(BaseModel):
    answer: str
    citations: list[EvidenceCitation]
    limitations: list[str] = Field(default_factory=list)
