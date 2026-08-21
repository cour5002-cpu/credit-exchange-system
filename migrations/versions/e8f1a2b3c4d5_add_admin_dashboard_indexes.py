"""add admin dashboard status indexes

Revision ID: e8f1a2b3c4d5
Revises: d7a8b9c0e1f2
Create Date: 2026-08-09 23:10:00.000000
"""
from alembic import op


revision = "e8f1a2b3c4d5"
down_revision = "d7a8b9c0e1f2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        "ix_college_tasks_status_created",
        "college_tasks",
        ["status", "created_at", "id"],
    )
    op.create_index(
        "ix_hour_applications_status_created",
        "hour_applications",
        ["status", "created_at", "id"],
    )
    op.create_index(
        "ix_credit_exchanges_status_created",
        "credit_exchange_applications",
        ["status", "created_at", "id"],
    )
    op.create_index(
        "ix_appeals_status_stage_created",
        "appeals",
        ["status", "reopen_stage", "created_at", "id"],
    )
    op.create_index(
        "ix_extension_requests_level_status_created",
        "extension_requests",
        ["review_level", "status", "created_at", "id"],
    )
    op.create_index(
        "ix_complaints_status_created",
        "complaints",
        ["status", "created_at", "id"],
    )


def downgrade():
    op.drop_index("ix_complaints_status_created", table_name="complaints")
    op.drop_index("ix_extension_requests_level_status_created", table_name="extension_requests")
    op.drop_index("ix_appeals_status_stage_created", table_name="appeals")
    op.drop_index("ix_credit_exchanges_status_created", table_name="credit_exchange_applications")
    op.drop_index("ix_hour_applications_status_created", table_name="hour_applications")
    op.drop_index("ix_college_tasks_status_created", table_name="college_tasks")
