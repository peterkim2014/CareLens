from dataclasses import dataclass

from pydantic import BaseModel, Field


@dataclass(frozen=True)
class EmbeddingRecord:
    document_id: str
    embedding: list[float]
    embedding_model: str
    content_hash: str


class SemanticSearchResult(BaseModel):
    document_id: str
    similarity: float = Field(
        ge=0.0,
        le=1.0,
    )


class SemanticIndexingResult(BaseModel):
    total_documents: int
    indexed_documents: int
    skipped_documents: int
