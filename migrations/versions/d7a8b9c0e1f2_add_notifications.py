"""add V2 notifications

Revision ID: d7a8b9c0e1f2
Revises: c6e4f8a1d2b3
Create Date: 2026-08-09 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "d7a8b9c0e1f2"
down_revision = "c6e4f8a1d2b3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("recipient_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("actor_user_id", sa.BigInteger(), sa.ForeignKey("users.id")),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("message_type", sa.String(64), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("biz_type", sa.String(64)),
        sa.Column("biz_id", sa.BigInteger()),
        sa.Column("payload", sa.JSON()),
        sa.Column("academic_year", sa.String(16), nullable=False),
        sa.Column("semester", sa.String(16), nullable=False),
        sa.Column("announcement_batch_key", sa.String(64)),
        sa.Column("announcement_audience", sa.String(255)),
        sa.Column("replaced_by_batch_key", sa.String(64)),
        sa.Column("expires_at", sa.DateTime()),
        sa.Column("stopped_at", sa.DateTime()),
        sa.Column("withdrawn_at", sa.DateTime()),
        sa.Column("dedupe_key", sa.String(200), nullable=False),
        sa.Column("read_at", sa.DateTime()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("recipient_user_id", "dedupe_key", name="uq_notifications_recipient_dedupe"),
    )
    op.create_index("ix_notifications_recipient_period_created", "notifications", ["recipient_user_id", "academic_year", "semester", "created_at", "id"])
    op.create_index("ix_notifications_recipient_period_read", "notifications", ["recipient_user_id", "academic_year", "semester", "read_at", "id"])
    op.create_index("ix_notifications_batch_recipient", "notifications", ["announcement_batch_key", "recipient_user_id"])
    op.create_index("ix_notifications_replaced_batch", "notifications", ["replaced_by_batch_key"])
    op.create_index("ix_notifications_business", "notifications", ["biz_type", "biz_id"])
    connection = op.get_bind()
    config_table = sa.table(
        "system_configs",
        sa.column("config_key", sa.String()),
        sa.column("config_value", sa.String()),
        sa.column("description", sa.String()),
    )
    existing = {
        row[0] for row in connection.execute(
            sa.select(config_table.c.config_key).where(
                config_table.c.config_key.in_(["current_academic_year", "current_semester"])
            )
        )
    }
    rows = [
        {"config_key": "current_academic_year", "config_value": "2026-2027", "description": "消息模块当前学年"},
        {"config_key": "current_semester", "config_value": "1", "description": "消息模块当前学期"},
    ]
    missing_rows = [row for row in rows if row["config_key"] not in existing]
    if missing_rows:
        op.bulk_insert(config_table, missing_rows)


def downgrade():
    op.drop_table("notifications")
