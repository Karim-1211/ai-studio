"""Add message attachments and social knowledge sources.

Revision ID: 20260628_0003
Revises: 20260628_0002
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0003"
down_revision = "20260628_0002"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "message_attachments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("message_id", sa.Integer(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=20), nullable=False),
        sa.Column("mime_type", sa.String(length=255), nullable=True),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("attachment_kind", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("extraction_method", sa.String(length=30), nullable=True),
        sa.Column("page_count", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"]),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename")
    )
    op.create_index(
        "ix_message_attachments_chat_id",
        "message_attachments",
        ["chat_id"],
        unique=False
    )
    op.create_index(
        "ix_message_attachments_message_id",
        "message_attachments",
        ["message_id"],
        unique=False
    )
    op.create_index(
        "ix_message_attachments_attachment_kind",
        "message_attachments",
        ["attachment_kind"],
        unique=False
    )
    op.create_index(
        "ix_message_attachments_status",
        "message_attachments",
        ["status"],
        unique=False
    )

    op.create_table(
        "message_attachment_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("attachment_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["attachment_id"],
            ["message_attachments.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "attachment_id",
            "chunk_index",
            name="uq_message_attachment_chunk_index"
        )
    )
    op.create_index(
        "ix_message_attachment_chunks_attachment_id",
        "message_attachment_chunks",
        ["attachment_id"],
        unique=False
    )

    op.create_table(
        "social_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(length=2048), nullable=False),
        sa.Column("canonical_url", sa.String(length=2048), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("platform", sa.String(length=50), nullable=False),
        sa.Column("domain", sa.String(length=255), nullable=False),
        sa.Column("extraction_method", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False),
        sa.Column("text_length", sa.Integer(), nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("content_type", sa.String(length=255), nullable=True),
        sa.Column("fetched_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
        sa.UniqueConstraint("canonical_url")
    )
    op.create_index(
        "ix_social_sources_platform",
        "social_sources",
        ["platform"],
        unique=False
    )
    op.create_index(
        "ix_social_sources_domain",
        "social_sources",
        ["domain"],
        unique=False
    )
    op.create_index(
        "ix_social_sources_status",
        "social_sources",
        ["status"],
        unique=False
    )

    op.create_table(
        "social_chunks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("social_source_id", sa.Integer(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["social_source_id"],
            ["social_sources.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "social_source_id",
            "chunk_index",
            name="uq_social_chunk_index"
        )
    )
    op.create_index(
        "ix_social_chunks_social_source_id",
        "social_chunks",
        ["social_source_id"],
        unique=False
    )


def downgrade():
    op.drop_index(
        "ix_social_chunks_social_source_id",
        table_name="social_chunks"
    )
    op.drop_table("social_chunks")

    op.drop_index("ix_social_sources_status", table_name="social_sources")
    op.drop_index("ix_social_sources_domain", table_name="social_sources")
    op.drop_index("ix_social_sources_platform", table_name="social_sources")
    op.drop_table("social_sources")

    op.drop_index(
        "ix_message_attachment_chunks_attachment_id",
        table_name="message_attachment_chunks"
    )
    op.drop_table("message_attachment_chunks")

    op.drop_index(
        "ix_message_attachments_status",
        table_name="message_attachments"
    )
    op.drop_index(
        "ix_message_attachments_attachment_kind",
        table_name="message_attachments"
    )
    op.drop_index(
        "ix_message_attachments_message_id",
        table_name="message_attachments"
    )
    op.drop_index(
        "ix_message_attachments_chat_id",
        table_name="message_attachments"
    )
    op.drop_table("message_attachments")
