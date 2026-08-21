"""add v3 registration contact phone

Revision ID: b1c2d3e4f5a6
Revises: a0b1c2d3e4f5
Create Date: 2026-08-10 10:20:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "b1c2d3e4f5a6"
down_revision = "a0b1c2d3e4f5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("task_registrations", sa.Column("contact_phone", sa.String(length=20), nullable=True))


def downgrade():
    op.drop_column("task_registrations", "contact_phone")
