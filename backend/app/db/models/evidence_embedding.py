from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)

from app.core.constants import (
    SEMANTIC_EMBEDDING_DIMENSIONS,
)
from app.db.base import Base


class EvidenceEmbeddingModel(Base):
    __tablename__ = "evidence_embeddings"

    document_id: Mapped[str] = mapped_column(
        String(255),
        ForeignKey(
            "evidence_documents.external_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    embedding: Mapped[list[float]] = mapped_column(
        Vector(
            SEMANTIC_EMBEDDING_DIMENSIONS,
        ),
        nullable=False,
    )

    embedding_model: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    content_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
