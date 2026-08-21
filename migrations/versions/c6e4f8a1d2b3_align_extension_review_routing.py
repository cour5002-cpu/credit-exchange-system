"""align extension review routing

Revision ID: c6e4f8a1d2b3
Revises: a3d7e9f1b2c4
Create Date: 2026-07-28 15:00:00.000000
"""
from datetime import timedelta
from math import ceil

from alembic import op
import sqlalchemy as sa


revision = "c6e4f8a1d2b3"
down_revision = "a3d7e9f1b2c4"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {item["name"] for item in inspector.get_columns("extension_requests")}
    if "extension_days" not in columns:
        op.add_column(
            "extension_requests",
            sa.Column("extension_days", sa.Integer(), nullable=True),
        )

    metadata = sa.MetaData()
    extensions = sa.Table(
        "extension_requests",
        metadata,
        sa.Column("id", sa.BigInteger()),
        sa.Column("application_id", sa.BigInteger()),
        sa.Column("old_due_at", sa.DateTime()),
        sa.Column("requested_due_at", sa.DateTime()),
        sa.Column("extension_days", sa.Integer()),
        sa.Column("review_level", sa.String(20)),
        sa.Column("status", sa.String(32)),
    )
    applications = sa.Table(
        "hour_applications",
        metadata,
        sa.Column("id", sa.BigInteger()),
        sa.Column("status", sa.String(32)),
    )

    pending_rows = bind.execute(
        sa.select(
            extensions.c.id,
            extensions.c.application_id,
            extensions.c.old_due_at,
            extensions.c.requested_due_at,
            extensions.c.status,
        )
    ).mappings().all()
    one_day_seconds = 24 * 60 * 60
    for row in pending_rows:
        delta = row["requested_due_at"] - row["old_due_at"]
        extension_days = max(1, ceil(delta.total_seconds() / one_day_seconds))
        is_special = delta > timedelta(days=30)
        values = {"extension_days": extension_days}
        if row["status"] in {
            "submitted",
            "pending_advisor_review",
            "pending_admin_review",
        }:
            values.update(
                review_level="admin" if is_special else "advisor",
                status="pending_admin_review" if is_special else "pending_advisor_review",
            )
            bind.execute(
                applications.update()
                .where(applications.c.id == row["application_id"])
                .values(status="extension_admin_review" if is_special else "extension_requested")
            )
        bind.execute(
            extensions.update()
            .where(extensions.c.id == row["id"])
            .values(**values)
        )

    op.alter_column(
        "extension_requests",
        "extension_days",
        existing_type=sa.Integer(),
        nullable=False,
    )
    op.alter_column(
        "extension_requests",
        "status",
        existing_type=sa.String(length=32),
        server_default="pending_advisor_review",
        existing_nullable=False,
    )
    op.execute(
        "UPDATE system_configs "
        "SET config_value = '30', description = '延期超过30天时转管理员审核（V1固定口径）' "
        "WHERE config_key = 'extension_special_threshold_days'"
    )


def downgrade():
    op.execute(
        "UPDATE extension_requests SET status = 'submitted' "
        "WHERE status IN ('pending_advisor_review', 'pending_admin_review')"
    )
    op.execute(
        "UPDATE system_configs "
        "SET config_value = '183', description = '延期超过该天数时转管理员审核' "
        "WHERE config_key = 'extension_special_threshold_days'"
    )
    op.alter_column(
        "extension_requests",
        "status",
        existing_type=sa.String(length=32),
        server_default="submitted",
        existing_nullable=False,
    )
    op.drop_column("extension_requests", "extension_days")
