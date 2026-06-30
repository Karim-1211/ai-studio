"""Add chat folders, tags, favorites, and archive state.

Revision ID: 20260628_0005
Revises: 20260628_0004
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0005"
down_revision = "20260628_0004"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "chat_folders",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_chat_folders_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "name",
            name="uq_chat_folders_user_name",
        ),
    )
    op.create_index(
        "ix_chat_folders_user_id",
        "chat_folders",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "chat_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("color", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_chat_tags_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "name",
            name="uq_chat_tags_user_name",
        ),
    )
    op.create_index(
        "ix_chat_tags_user_id",
        "chat_tags",
        ["user_id"],
        unique=False,
    )

    with op.batch_alter_table("chats") as batch_op:
        batch_op.add_column(sa.Column("folder_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "is_favorite",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.add_column(
            sa.Column(
                "is_archived",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            )
        )
        batch_op.create_foreign_key(
            "fk_chats_folder_id_chat_folders",
            "chat_folders",
            ["folder_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index("ix_chats_folder_id", ["folder_id"], unique=False)
        batch_op.create_index(
            "ix_chats_is_favorite",
            ["is_favorite"],
            unique=False,
        )
        batch_op.create_index(
            "ix_chats_is_archived",
            ["is_archived"],
            unique=False,
        )

    op.create_table(
        "chat_tag_links",
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["chat_id"],
            ["chats.id"],
            name="fk_chat_tag_links_chat_id_chats",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["chat_tags.id"],
            name="fk_chat_tag_links_tag_id_chat_tags",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("chat_id", "tag_id"),
    )

    with op.batch_alter_table("chats") as batch_op:
        batch_op.alter_column("is_favorite", server_default=None)
        batch_op.alter_column("is_archived", server_default=None)


def downgrade():
    op.drop_table("chat_tag_links")

    with op.batch_alter_table("chats") as batch_op:
        batch_op.drop_index("ix_chats_is_archived")
        batch_op.drop_index("ix_chats_is_favorite")
        batch_op.drop_index("ix_chats_folder_id")
        batch_op.drop_constraint(
            "fk_chats_folder_id_chat_folders",
            type_="foreignkey",
        )
        batch_op.drop_column("is_archived")
        batch_op.drop_column("is_favorite")
        batch_op.drop_column("folder_id")

    op.drop_index("ix_chat_tags_user_id", table_name="chat_tags")
    op.drop_table("chat_tags")
    op.drop_index("ix_chat_folders_user_id", table_name="chat_folders")
    op.drop_table("chat_folders")
