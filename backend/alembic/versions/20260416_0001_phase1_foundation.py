"""Phase 1 foundation schema

Revision ID: 20260416_0001
Revises:
Create Date: 2026-04-16 18:00:00
"""

from __future__ import annotations

from alembic import context, op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260416_0001"
down_revision = None
branch_labels = None
depends_on = None


review_status_enum = sa.Enum(
    "PENDING_REVIEW",
    "APPROVED",
    "REJECTED",
    name="document_review_status",
    native_enum=False,
)
processing_status_enum = sa.Enum(
    "QUEUED",
    "PARSING",
    "FACTS_READY",
    "FAILED",
    name="document_processing_status",
    native_enum=False,
)
indexing_status_enum = sa.Enum(
    "NOT_INDEXED",
    "QUEUED",
    "INDEXING",
    "INDEXED",
    "FAILED",
    name="document_indexing_status",
    native_enum=False,
)
extraction_run_status_enum = sa.Enum(
    "QUEUED",
    "RUNNING",
    "SUCCEEDED",
    "FAILED",
    name="extraction_run_status",
    native_enum=False,
)
json_document_type = sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql")


def _has_table(inspector, table_name: str) -> bool:
    return table_name in inspector.get_table_names()


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return column_name in {column["name"] for column in inspector.get_columns(table_name)}


def _has_index(inspector, table_name: str, index_name: str) -> bool:
    return index_name in {index["name"] for index in inspector.get_indexes(table_name)}


def _create_fresh_schema() -> None:
    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=True, server_default=sa.false()),
    )
    op.create_index("ix_user_id", "user", ["id"], unique=False)
    op.create_index("ix_user_username", "user", ["username"], unique=True)

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("result_tree_json", sa.JSON(), nullable=False),
        sa.Column("selected_node_id", sa.String(), nullable=True),
        sa.Column("expanded_node_ids", sa.JSON(), nullable=False),
        sa.Column("view_mode", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("last_message_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_chat_sessions_id", "chat_sessions", ["id"], unique=False)
    op.create_index("ix_chat_sessions_owner_id", "chat_sessions", ["owner_id"], unique=False)

    op.create_table(
        "chat_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("session_id", sa.Integer(), sa.ForeignKey("chat_sessions.id"), nullable=False),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("meta", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_chat_messages_id", "chat_messages", ["id"], unique=False)
    op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"], unique=False)

    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("file_path", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False, server_default="application/pdf"),
        sa.Column("file_size_bytes", sa.Integer(), nullable=False),
        sa.Column("review_status", review_status_enum, nullable=False, server_default="PENDING_REVIEW"),
        sa.Column("processing_status", processing_status_enum, nullable=False, server_default="QUEUED"),
        sa.Column("indexing_status", indexing_status_enum, nullable=False, server_default="NOT_INDEXED"),
        sa.Column("active_extraction_version", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("batch_id", sa.String(), nullable=True),
        sa.Column("ingestion_source", sa.String(), nullable=True),
        sa.Column("queue_priority", sa.String(), nullable=True),
        sa.Column("trusted_import", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
    )
    op.create_index("ix_documents_id", "documents", ["id"], unique=False)
    op.create_index("ix_documents_title", "documents", ["title"], unique=False)
    op.create_index("ix_documents_owner_id", "documents", ["owner_id"], unique=False)
    op.create_index("ix_documents_batch_id", "documents", ["batch_id"], unique=False)

    op.create_table(
        "contract_facts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("extraction_version", sa.Integer(), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("facts", json_document_type, nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("document_id", "extraction_version", name="uq_contract_facts_document_version"),
    )
    op.create_index("ix_contract_facts_document_id", "contract_facts", ["document_id"], unique=False)

    op.create_table(
        "extraction_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("extraction_version", sa.Integer(), nullable=False),
        sa.Column("status", extraction_run_status_enum, nullable=False, server_default="QUEUED"),
        sa.Column("error_details", json_document_type, nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_extraction_runs_document_id", "extraction_runs", ["document_id"], unique=False)
    op.create_index("ix_extraction_runs_status", "extraction_runs", ["status"], unique=False)


def upgrade() -> None:
    if context.is_offline_mode():
        _create_fresh_schema()
        return

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if not _has_table(inspector, "user"):
        op.create_table(
            "user",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("username", sa.String(), nullable=False),
            sa.Column("hashed_password", sa.String(), nullable=False),
            sa.Column("is_admin", sa.Boolean(), nullable=True, server_default=sa.false()),
        )
        op.create_index("ix_user_id", "user", ["id"], unique=False)
        op.create_index("ix_user_username", "user", ["username"], unique=True)
        inspector = sa.inspect(bind)

    if not _has_table(inspector, "chat_sessions"):
        op.create_table(
            "chat_sessions",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("result_tree_json", sa.JSON(), nullable=False),
            sa.Column("selected_node_id", sa.String(), nullable=True),
            sa.Column("expanded_node_ids", sa.JSON(), nullable=False),
            sa.Column("view_mode", sa.String(), nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("last_message_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_chat_sessions_id", "chat_sessions", ["id"], unique=False)
        op.create_index("ix_chat_sessions_owner_id", "chat_sessions", ["owner_id"], unique=False)
        inspector = sa.inspect(bind)

    if not _has_table(inspector, "chat_messages"):
        op.create_table(
            "chat_messages",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("session_id", sa.Integer(), sa.ForeignKey("chat_sessions.id"), nullable=False),
            sa.Column("role", sa.String(), nullable=False),
            sa.Column("content", sa.Text(), nullable=False),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_chat_messages_id", "chat_messages", ["id"], unique=False)
        op.create_index("ix_chat_messages_session_id", "chat_messages", ["session_id"], unique=False)
        inspector = sa.inspect(bind)

    if _has_table(inspector, "document") and not _has_table(inspector, "documents"):
        op.rename_table("document", "documents")
        inspector = sa.inspect(bind)

    if not _has_table(inspector, "documents"):
        op.create_table(
            "documents",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("title", sa.String(), nullable=False),
            sa.Column("file_path", sa.String(), nullable=False),
            sa.Column("content_type", sa.String(), nullable=False, server_default="application/pdf"),
            sa.Column("file_size_bytes", sa.Integer(), nullable=False),
            sa.Column("review_status", review_status_enum, nullable=False, server_default="PENDING_REVIEW"),
            sa.Column("processing_status", processing_status_enum, nullable=False, server_default="QUEUED"),
            sa.Column("indexing_status", indexing_status_enum, nullable=False, server_default="NOT_INDEXED"),
            sa.Column("active_extraction_version", sa.Integer(), nullable=True),
            sa.Column("last_error", sa.String(), nullable=True),
            sa.Column("batch_id", sa.String(), nullable=True),
            sa.Column("ingestion_source", sa.String(), nullable=True),
            sa.Column("queue_priority", sa.String(), nullable=True),
            sa.Column("trusted_import", sa.Boolean(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("owner_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False),
        )
        inspector = sa.inspect(bind)
    else:
        if not _has_column(inspector, "documents", "content_type"):
            op.add_column("documents", sa.Column("content_type", sa.String(), nullable=False, server_default="application/pdf"))
        if not _has_column(inspector, "documents", "file_size_bytes"):
            op.add_column("documents", sa.Column("file_size_bytes", sa.Integer(), nullable=False, server_default="0"))
        if not _has_column(inspector, "documents", "review_status"):
            op.add_column("documents", sa.Column("review_status", review_status_enum, nullable=False, server_default="PENDING_REVIEW"))
        if not _has_column(inspector, "documents", "processing_status"):
            op.add_column("documents", sa.Column("processing_status", processing_status_enum, nullable=False, server_default="QUEUED"))
        if not _has_column(inspector, "documents", "indexing_status"):
            op.add_column("documents", sa.Column("indexing_status", indexing_status_enum, nullable=False, server_default="NOT_INDEXED"))
        if not _has_column(inspector, "documents", "active_extraction_version"):
            op.add_column("documents", sa.Column("active_extraction_version", sa.Integer(), nullable=True))
        if not _has_column(inspector, "documents", "last_error"):
            op.add_column("documents", sa.Column("last_error", sa.String(), nullable=True))
        if not _has_column(inspector, "documents", "batch_id"):
            op.add_column("documents", sa.Column("batch_id", sa.String(), nullable=True))
        if not _has_column(inspector, "documents", "ingestion_source"):
            op.add_column("documents", sa.Column("ingestion_source", sa.String(), nullable=True))
        if not _has_column(inspector, "documents", "queue_priority"):
            op.add_column("documents", sa.Column("queue_priority", sa.String(), nullable=True))
        if not _has_column(inspector, "documents", "trusted_import"):
            op.add_column("documents", sa.Column("trusted_import", sa.Boolean(), nullable=True))
        if not _has_column(inspector, "documents", "updated_at"):
            op.add_column("documents", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

        if _has_column(inspector, "documents", "status"):
            op.execute(
                sa.text(
                    """
                    UPDATE documents
                    SET review_status = CASE
                        WHEN status = 'CONFIRMED' THEN 'APPROVED'
                        ELSE 'PENDING_REVIEW'
                    END
                    WHERE review_status IS NULL OR review_status = 'PENDING_REVIEW'
                    """
                )
            )
        inspector = sa.inspect(bind)

    if not _has_index(inspector, "documents", "ix_documents_id"):
        op.create_index("ix_documents_id", "documents", ["id"], unique=False)
    if not _has_index(inspector, "documents", "ix_documents_title"):
        op.create_index("ix_documents_title", "documents", ["title"], unique=False)
    if not _has_index(inspector, "documents", "ix_documents_owner_id"):
        op.create_index("ix_documents_owner_id", "documents", ["owner_id"], unique=False)
    if not _has_index(inspector, "documents", "ix_documents_batch_id"):
        op.create_index("ix_documents_batch_id", "documents", ["batch_id"], unique=False)

    if not _has_table(inspector, "contract_facts"):
        op.create_table(
            "contract_facts",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("extraction_version", sa.Integer(), nullable=False),
            sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("facts", json_document_type, nullable=False),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.UniqueConstraint("document_id", "extraction_version", name="uq_contract_facts_document_version"),
        )
        op.create_index("ix_contract_facts_document_id", "contract_facts", ["document_id"], unique=False)

    inspector = sa.inspect(bind)
    if not _has_table(inspector, "extraction_runs"):
        op.create_table(
            "extraction_runs",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("document_id", sa.Integer(), sa.ForeignKey("documents.id", ondelete="CASCADE"), nullable=False),
            sa.Column("extraction_version", sa.Integer(), nullable=False),
            sa.Column("status", extraction_run_status_enum, nullable=False, server_default="QUEUED"),
            sa.Column("error_details", json_document_type, nullable=True),
            sa.Column("started_at", sa.DateTime(), nullable=True),
            sa.Column("completed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        )
        op.create_index("ix_extraction_runs_document_id", "extraction_runs", ["document_id"], unique=False)
        op.create_index("ix_extraction_runs_status", "extraction_runs", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_extraction_runs_status", table_name="extraction_runs")
    op.drop_index("ix_extraction_runs_document_id", table_name="extraction_runs")
    op.drop_table("extraction_runs")

    op.drop_index("ix_contract_facts_document_id", table_name="contract_facts")
    op.drop_table("contract_facts")

    op.drop_index("ix_documents_batch_id", table_name="documents")
    op.drop_index("ix_documents_owner_id", table_name="documents")
    op.drop_index("ix_documents_title", table_name="documents")
    op.drop_index("ix_documents_id", table_name="documents")
    op.drop_table("documents")

    op.drop_index("ix_chat_messages_session_id", table_name="chat_messages")
    op.drop_index("ix_chat_messages_id", table_name="chat_messages")
    op.drop_table("chat_messages")

    op.drop_index("ix_chat_sessions_owner_id", table_name="chat_sessions")
    op.drop_index("ix_chat_sessions_id", table_name="chat_sessions")
    op.drop_table("chat_sessions")

    op.drop_index("ix_user_username", table_name="user")
    op.drop_index("ix_user_id", table_name="user")
    op.drop_table("user")
