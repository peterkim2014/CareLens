"""remove redundant evidence document unique constraint

Revision ID: 828fa2c081c6
Revises: 9a8018383224
Create Date: 2026-07-28 23:56:18.209350

"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "828fa2c081c6"
down_revision: str | Sequence[str] | None = "9a8018383224"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        "fk_evidence_embeddings_document_id_evidence_documents",
        "evidence_embeddings",
        type_="foreignkey",
    )

    op.drop_constraint(
        "uq_evidence_documents_external_id",
        "evidence_documents",
        type_="unique",
    )

    op.create_foreign_key(
        "fk_evidence_embeddings_document_id_evidence_documents",
        "evidence_embeddings",
        "evidence_documents",
        ["document_id"],
        ["external_id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "fk_evidence_embeddings_document_id_evidence_documents",
        "evidence_embeddings",
        type_="foreignkey",
    )

    op.create_unique_constraint(
        "uq_evidence_documents_external_id",
        "evidence_documents",
        ["external_id"],
    )

    op.create_foreign_key(
        "fk_evidence_embeddings_document_id_evidence_documents",
        "evidence_embeddings",
        "evidence_documents",
        ["document_id"],
        ["external_id"],
        ondelete="CASCADE",
    )
