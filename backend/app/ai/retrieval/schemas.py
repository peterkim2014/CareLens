from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class EmbeddingRecord:
    document_id: str
    embedding: list[float]
    embedding_model: str
    content_hash: str


class EvidenceDocument(BaseModel):
    document_id: str
    title: str
    content: str
    source: str
    source_type: str
    metadata: dict[str, str] = Field(default_factory=dict)


class RetrievedEvidence(BaseModel):
    document_id: str
    title: str
    content: str
    source: str
    source_type: str
    score: float = Field(ge=0.0, le=1.0)
    matched_terms: list[str] = Field(default_factory=list)
    metadata: dict[str, str] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    query: str
    total_candidates: int = Field(ge=0)
    evidence: list[RetrievedEvidence] = Field(
        default_factory=list,
    )
