"""complete week3 drafts and extensions

Revision ID: d8f3a1c6e2b4
Revises: b7e6c9d2a5f1
Create Date: 2026-07-20 18:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "d8f3a1c6e2b4"
down_revision = "b7e6c9d2a5f1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "extension_requests",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("hour_applications.id"), nullable=False, unique=True),
        sa.Column("old_due_at", sa.DateTime(), nullable=False),
        sa.Column("requested_due_at", sa.DateTime(), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("review_level", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="submitted"),
        sa.Column("reviewed_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("review_comment", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
    )


def downgrade():
    op.drop_table("extension_requests")
