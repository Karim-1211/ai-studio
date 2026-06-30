"""Add indexed website knowledge sources.

Revision ID: 20260628_0002
Revises: 20260628_0001
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0002"
down_revision = "20260628_0001"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "website_sources",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "url",
            sa.String(length=2048),
            nullable=False
        ),
        sa.Column(
            "canonical_url",
            sa.String(length=2048),
            nullable=False
        ),
        sa.Column(
            "title",
            sa.String(length=500),
            nullable=False
        ),
        sa.Column(
            "domain",
            sa.String(length=255),
            nullable=False
        ),
        sa.Column(
            "status",
            sa.String(length=30),
            nullable=False
        ),
        sa.Column(
            "error_message",
            sa.Text(),
            nullable=True
        ),
        sa.Column(
            "chunk_count",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "text_length",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "http_status",
            sa.Integer(),
            nullable=True
        ),
        sa.Column(
            "content_type",
            sa.String(length=255),
            nullable=True
        ),
        sa.Column(
            "fetched_at",
            sa.DateTime(),
            nullable=True
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("url"),
        sa.UniqueConstraint("canonical_url")
    )

    op.create_index(
        "ix_website_sources_domain",
        "website_sources",
        ["domain"],
        unique=False
    )

    op.create_index(
        "ix_website_sources_status",
        "website_sources",
        ["status"],
        unique=False
    )

    op.create_table(
        "website_chunks",
        sa.Column(
            "id",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "website_source_id",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "chunk_index",
            sa.Integer(),
            nullable=False
        ),
        sa.Column(
            "content",
            sa.Text(),
            nullable=False
        ),
        sa.Column(
            "embedding",
            sa.JSON(),
            nullable=False
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["website_source_id"],
            ["website_sources.id"]
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "website_source_id",
            "chunk_index",
            name="uq_website_chunk_index"
        )
    )

    op.create_index(
        "ix_website_chunks_website_source_id",
        "website_chunks",
        ["website_source_id"],
        unique=False
    )


def downgrade():
    op.drop_index(
        "ix_website_chunks_website_source_id",
        table_name="website_chunks"
    )
    op.drop_table("website_chunks")

    op.drop_index(
        "ix_website_sources_status",
        table_name="website_sources"
    )
    op.drop_index(
        "ix_website_sources_domain",
        table_name="website_sources"
    )
    op.drop_table("website_sources")
