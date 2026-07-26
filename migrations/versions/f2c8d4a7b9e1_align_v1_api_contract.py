"""align v1 api contract

Revision ID: f2c8d4a7b9e1
Revises: e9a4b2c7d1f6
Create Date: 2026-07-21 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "f2c8d4a7b9e1"
down_revision = "e9a4b2c7d1f6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("attachments") as batch_op:
        batch_op.add_column(sa.Column("voided_by", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("voided_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("void_reason", sa.Text(), nullable=True))
        batch_op.create_foreign_key(
            "fk_attachments_voided_by_users",
            "users",
            ["voided_by"],
            ["id"],
        )

    with op.batch_alter_table("credit_exchange_applications") as batch_op:
        batch_op.alter_column(
            "estimated_credits",
            existing_type=sa.Numeric(10, 2),
            nullable=True,
        )

    with op.batch_alter_table("credit_exchange_allocations") as batch_op:
        batch_op.alter_column(
            "allocated_credits",
            existing_type=sa.Numeric(10, 2),
            nullable=True,
        )


def downgrade():
    op.execute("UPDATE credit_exchange_allocations SET allocated_credits = 0 WHERE allocated_credits IS NULL")
    with op.batch_alter_table("credit_exchange_allocations") as batch_op:
        batch_op.alter_column(
            "allocated_credits",
            existing_type=sa.Numeric(10, 2),
            nullable=False,
        )

    op.execute("UPDATE credit_exchange_applications SET estimated_credits = 0 WHERE estimated_credits IS NULL")
    with op.batch_alter_table("credit_exchange_applications") as batch_op:
        batch_op.alter_column(
            "estimated_credits",
            existing_type=sa.Numeric(10, 2),
            nullable=False,
        )

    with op.batch_alter_table("attachments") as batch_op:
        batch_op.drop_constraint("fk_attachments_voided_by_users", type_="foreignkey")
        batch_op.drop_column("void_reason")
        batch_op.drop_column("voided_at")
        batch_op.drop_column("voided_by")
