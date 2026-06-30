"""Add admin analytics, health history, model usage, and audit logs.

Revision ID: 20260628_0007
Revises: 20260628_0006
Create Date: 2026-06-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260628_0007"
down_revision = "20260628_0006"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "request_metrics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=False),
        sa.Column("method", sa.String(length=12), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("endpoint", sa.String(length=160), nullable=True),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("is_error", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_request_metrics_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("request_id", name="uq_request_metrics_request_id"),
    )
    for column in ("user_id", "request_id", "path", "endpoint", "status_code", "is_error", "created_at"):
        op.create_index(f"ix_request_metrics_{column}", "request_metrics", [column], unique=False)

    op.create_table(
        "model_usage_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("chat_id", sa.Integer(), nullable=True),
        sa.Column("request_id", sa.String(length=64), nullable=True),
        sa.Column("model", sa.String(length=200), nullable=False),
        sa.Column("mode", sa.String(length=50), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("used_rag", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_message", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"],
            name="fk_model_usage_events_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["chat_id"], ["chats.id"],
            name="fk_model_usage_events_chat_id_chats",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("user_id", "chat_id", "request_id", "model", "mode", "success", "used_rag", "created_at"):
        op.create_index(f"ix_model_usage_events_{column}", "model_usage_events", [column], unique=False)

    op.create_table(
        "health_check_events",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False),
        sa.Column("ready", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("components", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("status", "ready", "created_at"):
        op.create_index(f"ix_health_check_events_{column}", "health_check_events", [column], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("actor_user_id", sa.Integer(), nullable=True),
        sa.Column("target_user_id", sa.Integer(), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=True),
        sa.Column("entity_id", sa.String(length=120), nullable=True),
        sa.Column("details", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["actor_user_id"], ["users.id"],
            name="fk_audit_logs_actor_user_id_users",
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["target_user_id"], ["users.id"],
            name="fk_audit_logs_target_user_id_users",
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    for column in ("actor_user_id", "target_user_id", "action", "entity_type", "created_at"):
        op.create_index(f"ix_audit_logs_{column}", "audit_logs", [column], unique=False)

    with op.batch_alter_table("request_metrics") as batch_op:
        batch_op.alter_column("is_error", server_default=None)
    with op.batch_alter_table("model_usage_events") as batch_op:
        batch_op.alter_column("success", server_default=None)
        batch_op.alter_column("used_rag", server_default=None)
        batch_op.alter_column("source_count", server_default=None)
    with op.batch_alter_table("health_check_events") as batch_op:
        batch_op.alter_column("ready", server_default=None)


def downgrade():
    for column in ("created_at", "entity_type", "action", "target_user_id", "actor_user_id"):
        op.drop_index(f"ix_audit_logs_{column}", table_name="audit_logs")
    op.drop_table("audit_logs")

    for column in ("created_at", "ready", "status"):
        op.drop_index(f"ix_health_check_events_{column}", table_name="health_check_events")
    op.drop_table("health_check_events")

    for column in ("created_at", "used_rag", "success", "mode", "model", "request_id", "chat_id", "user_id"):
        op.drop_index(f"ix_model_usage_events_{column}", table_name="model_usage_events")
    op.drop_table("model_usage_events")

    for column in ("created_at", "is_error", "status_code", "endpoint", "path", "request_id", "user_id"):
        op.drop_index(f"ix_request_metrics_{column}", table_name="request_metrics")
    op.drop_table("request_metrics")
