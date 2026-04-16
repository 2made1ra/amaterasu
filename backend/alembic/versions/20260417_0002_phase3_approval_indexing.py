"""Phase 3 approval and indexing audit fields

Revision ID: 20260417_0002
Revises: 20260416_0001
Create Date: 2026-04-17 10:30:00
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa


revision = "20260417_0002"
down_revision = "20260416_0001"
branch_labels = None
depends_on = None


approval_source_enum = sa.Enum(
    "MANUAL",
    "TRUSTED_IMPORT",
    name="document_approval_source",
    native_enum=False,
)


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def upgrade() -> None:
    if context.is_offline_mode():
        op.add_column("documents", sa.Column("approval_source", approval_source_enum, nullable=True))
        op.add_column("documents", sa.Column("approved_at", sa.DateTime(), nullable=True))
        op.add_column("documents", sa.Column("approved_by_user_id", sa.Integer(), nullable=True))
        op.create_index("ix_documents_approved_by_user_id", "documents", ["approved_by_user_id"], unique=False)
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_column(inspector, "documents", "approval_source"):
        op.add_column("documents", sa.Column("approval_source", approval_source_enum, nullable=True))
        inspector = sa.inspect(bind)
    if not _has_column(inspector, "documents", "approved_at"):
        op.add_column("documents", sa.Column("approved_at", sa.DateTime(), nullable=True))
        inspector = sa.inspect(bind)
    if not _has_column(inspector, "documents", "approved_by_user_id"):
        op.add_column("documents", sa.Column("approved_by_user_id", sa.Integer(), nullable=True))
        inspector = sa.inspect(bind)
    if not _has_index(inspector, "documents", "ix_documents_approved_by_user_id"):
        op.create_index("ix_documents_approved_by_user_id", "documents", ["approved_by_user_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if _has_index(inspector, "documents", "ix_documents_approved_by_user_id"):
        op.drop_index("ix_documents_approved_by_user_id", table_name="documents")
        inspector = sa.inspect(bind)
    if _has_column(inspector, "documents", "approved_by_user_id"):
        op.drop_column("documents", "approved_by_user_id")
        inspector = sa.inspect(bind)
    if _has_column(inspector, "documents", "approved_at"):
        op.drop_column("documents", "approved_at")
        inspector = sa.inspect(bind)
    if _has_column(inspector, "documents", "approval_source"):
        op.drop_column("documents", "approval_source")
