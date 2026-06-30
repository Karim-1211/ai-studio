"""Add prompt library and conversation branching metadata.

Revision ID: 20260628_0006
Revises: 20260628_0005
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0006"
down_revision = "20260628_0005"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "prompt_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column(
            "is_favorite",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
        sa.Column(
            "usage_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
            name="fk_prompt_templates_user_id_users",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "title",
            name="uq_prompt_templates_user_title",
        ),
    )
    op.create_index(
        "ix_prompt_templates_user_id",
        "prompt_templates",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_prompt_templates_category",
        "prompt_templates",
        ["category"],
        unique=False,
    )
    op.create_index(
        "ix_prompt_templates_is_favorite",
        "prompt_templates",
        ["is_favorite"],
        unique=False,
    )

    with op.batch_alter_table("chats") as batch_op:
        batch_op.add_column(
            sa.Column("parent_chat_id", sa.Integer(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("branched_from_message_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_chats_parent_chat_id_chats",
            "chats",
            ["parent_chat_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_foreign_key(
            "fk_chats_branched_from_message_id_messages",
            "messages",
            ["branched_from_message_id"],
            ["id"],
            ondelete="SET NULL",
        )
        batch_op.create_index(
            "ix_chats_parent_chat_id",
            ["parent_chat_id"],
            unique=False,
        )
        batch_op.create_index(
            "ix_chats_branched_from_message_id",
            ["branched_from_message_id"],
            unique=False,
        )

    with op.batch_alter_table("prompt_templates") as batch_op:
        batch_op.alter_column("is_favorite", server_default=None)
        batch_op.alter_column("usage_count", server_default=None)


def downgrade():
    with op.batch_alter_table("chats") as batch_op:
        batch_op.drop_index("ix_chats_branched_from_message_id")
        batch_op.drop_index("ix_chats_parent_chat_id")
        batch_op.drop_constraint(
            "fk_chats_branched_from_message_id_messages",
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            "fk_chats_parent_chat_id_chats",
            type_="foreignkey",
        )
        batch_op.drop_column("branched_from_message_id")
        batch_op.drop_column("parent_chat_id")

    op.drop_index(
        "ix_prompt_templates_is_favorite",
        table_name="prompt_templates",
    )
    op.drop_index(
        "ix_prompt_templates_category",
        table_name="prompt_templates",
    )
    op.drop_index(
        "ix_prompt_templates_user_id",
        table_name="prompt_templates",
    )
    op.drop_table("prompt_templates")
