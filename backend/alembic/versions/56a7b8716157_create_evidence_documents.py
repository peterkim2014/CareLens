"""create evidence documents

Revision ID: 56a7b8716157
Revises:
Create Date: REPLACE_WITH_YOUR_GENERATED_DATE
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "56a7b8716157"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "evidence_documents",
        sa.Column(
            "id",
            sa.Uuid(),
            nullable=False,
        ),
        sa.Column(
            "external_id",
            sa.String(length=100),
            nullable=False,
        ),
        sa.Column(
            "title",
            sa.String(length=500),
            nullable=False,
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False,
        ),
        sa.Column(
            "source_name",
            sa.String(length=255),
            nullable=False,
        ),
        sa.Column(
            "source_url",
            sa.String(length=2048),
            nullable=True,
        ),
        sa.Column(
            "publication_date",
            sa.Date(),
            nullable=True,
        ),
        sa.Column(
            "reviewed_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "review_status",
            sa.Enum(
                "draft",
                "approved",
                "rejected",
                "archived",
                name="evidence_review_status",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column(
            "specialty",
            sa.String(length=100),
            nullable=True,
        ),
        sa.Column(
            "keywords",
            postgresql.JSONB(
                astext_type=sa.Text(),
            ),
            nullable=False,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name=op.f(
                "pk_evidence_documents",
            ),
        ),
        sa.UniqueConstraint(
            "external_id",
            name=op.f(
                "uq_evidence_documents_external_id",
            ),
        ),
    )

    op.create_index(
        "ix_evidence_documents_active_review_status",
        "evidence_documents",
        [
            "is_active",
            "review_status",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_evidence_documents_external_id",
        ),
        "evidence_documents",
        [
            "external_id",
        ],
        unique=True,
    )

    op.create_index(
        op.f(
            "ix_evidence_documents_is_active",
        ),
        "evidence_documents",
        [
            "is_active",
        ],
        unique=False,
    )

    op.create_index(
        op.f(
            "ix_evidence_documents_review_status",
        ),
        "evidence_documents",
        [
            "review_status",
        ],
        unique=False,
    )

    op.create_index(
        "ix_evidence_documents_specialty",
        "evidence_documents",
        [
            "specialty",
        ],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_evidence_documents_specialty",
        table_name="evidence_documents",
    )

    op.drop_index(
        op.f(
            "ix_evidence_documents_review_status",
        ),
        table_name="evidence_documents",
    )

    op.drop_index(
        op.f(
            "ix_evidence_documents_is_active",
        ),
        table_name="evidence_documents",
    )

    op.drop_index(
        op.f(
            "ix_evidence_documents_external_id",
        ),
        table_name="evidence_documents",
    )

    op.drop_index(
        "ix_evidence_documents_active_review_status",
        table_name="evidence_documents",
    )

    op.drop_table(
        "evidence_documents",
    )
