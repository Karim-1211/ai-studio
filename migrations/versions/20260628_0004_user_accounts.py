"""Add secure user accounts and workspace ownership.

Revision ID: 20260628_0004
Revises: 20260628_0003
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0004"
down_revision = "20260628_0003"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=120), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False),
        sa.Column("failed_login_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(), nullable=True),
        sa.Column("last_login_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_active", "users", ["active"], unique=False)
    op.create_index("ix_users_is_admin", "users", ["is_admin"], unique=False)

    with op.batch_alter_table("chats") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_chats_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index("ix_chats_user_id", ["user_id"], unique=False)

    with op.batch_alter_table("global_documents") as batch_op:
        batch_op.add_column(sa.Column("user_id", sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            "fk_global_documents_user_id_users",
            "users",
            ["user_id"],
            ["id"],
            ondelete="CASCADE",
        )
        batch_op.create_index(
            "ix_global_documents_user_id",
            ["user_id"],
            unique=False,
        )

    op.create_table(
        "user_website_sources",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("website_source_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_website_sources_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["website_source_id"],
            ["website_sources.id"],
            name="fk_user_website_sources_website_source_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "website_source_id"),
    )
    op.create_index(
        "ix_user_website_sources_website_source_id",
        "user_website_sources",
        ["website_source_id"],
        unique=False,
    )

    op.create_table(
        "user_social_sources",
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("social_source_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_user_social_sources_user_id",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["social_source_id"],
            ["social_sources.id"],
            name="fk_user_social_sources_social_source_id",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "social_source_id"),
    )
    op.create_index(
        "ix_user_social_sources_social_source_id",
        "user_social_sources",
        ["social_source_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        "ix_user_social_sources_social_source_id",
        table_name="user_social_sources",
    )
    op.drop_table("user_social_sources")

    op.drop_index(
        "ix_user_website_sources_website_source_id",
        table_name="user_website_sources",
    )
    op.drop_table("user_website_sources")

    with op.batch_alter_table("global_documents") as batch_op:
        batch_op.drop_index("ix_global_documents_user_id")
        batch_op.drop_constraint(
            "fk_global_documents_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("user_id")

    with op.batch_alter_table("chats") as batch_op:
        batch_op.drop_index("ix_chats_user_id")
        batch_op.drop_constraint(
            "fk_chats_user_id_users",
            type_="foreignkey",
        )
        batch_op.drop_column("user_id")

    op.drop_index("ix_users_is_admin", table_name="users")
    op.drop_index("ix_users_active", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
