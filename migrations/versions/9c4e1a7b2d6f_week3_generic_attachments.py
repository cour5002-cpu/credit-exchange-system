"""week3 generic attachments

Revision ID: 9c4e1a7b2d6f
Revises: 7b3d3f2e9a1c
Create Date: 2026-07-14 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "9c4e1a7b2d6f"
down_revision = "7b3d3f2e9a1c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "attachments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("biz_type", sa.String(length=64), nullable=False),
        sa.Column("owner_type", sa.String(length=64), nullable=True),
        sa.Column("owner_id", sa.BigInteger(), nullable=True),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("uploaded_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )


def downgrade():
    op.drop_table("attachments")
