from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID, uuid4

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Enum,
    Index,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Dialect
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.type_api import TypeEngine
from sqlalchemy.types import JSON, TypeDecorator

from app.db.base import Base


class ReviewStatus(StrEnum):
    DRAFT = "draft"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"


class JSONList(TypeDecorator[list[str]]):
    impl = JSON
    cache_ok = True

    def load_dialect_impl(
        self,
        dialect: Dialect,
    ) -> TypeEngine[object]:
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())

        return dialect.type_descriptor(JSON())


class EvidenceDocumentModel(Base):
    __tablename__ = "evidence_documents"
    __table_args__ = (
        Index(
            "ix_evidence_documents_active_review_status",
            "is_active",
            "review_status",
        ),
        Index(
            "ix_evidence_documents_specialty",
            "specialty",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        primary_key=True,
        default=uuid4,
    )

    external_id: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    source_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    source_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    publication_date: Mapped[date | None] = mapped_column(
        Date,
        nullable=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    review_status: Mapped[ReviewStatus] = mapped_column(
        Enum(
            ReviewStatus,
            name="evidence_review_status",
            native_enum=False,
            validate_strings=True,
        ),
        nullable=False,
        default=ReviewStatus.DRAFT,
        index=True,
    )

    specialty: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    keywords: Mapped[list[str]] = mapped_column(
        JSONList(),
        nullable=False,
        default=list,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
