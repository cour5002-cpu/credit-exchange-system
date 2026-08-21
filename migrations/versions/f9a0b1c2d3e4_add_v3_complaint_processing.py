"""add v3 complaint processing

Revision ID: f9a0b1c2d3e4
Revises: e8f1a2b3c4d5
Create Date: 2026-08-10 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "f9a0b1c2d3e4"
down_revision = "e8f1a2b3c4d5"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("complaints", sa.Column("complaint_no", sa.String(length=64), nullable=True))
    op.add_column("complaints", sa.Column("category", sa.String(length=32), nullable=True))
    op.add_column("complaints", sa.Column("processing_started_at", sa.DateTime(), nullable=True))
    op.add_column("complaints", sa.Column("handled_by", sa.BigInteger(), nullable=True))
    op.add_column("complaints", sa.Column("handling_result", sa.String(length=32), nullable=True))
    op.add_column("complaints", sa.Column("handling_opinion", sa.Text(), nullable=True))
    op.add_column("complaints", sa.Column("handled_at", sa.DateTime(), nullable=True))
    op.add_column(
        "complaints",
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=True),
    )
    op.create_foreign_key(
        "fk_complaints_handled_by_users",
        "complaints",
        "users",
        ["handled_by"],
        ["id"],
    )

    bind = op.get_bind()
    complaints = sa.table(
        "complaints",
        sa.column("id", sa.BigInteger()),
        sa.column("complaint_no", sa.String(64)),
        sa.column("category", sa.String(32)),
        sa.column("status", sa.String(20)),
        sa.column("viewed_at", sa.DateTime()),
        sa.column("processing_started_at", sa.DateTime()),
        sa.column("created_at", sa.DateTime()),
        sa.column("updated_at", sa.DateTime()),
    )
    rows = bind.execute(
        sa.select(
            complaints.c.id,
            complaints.c.status,
            complaints.c.viewed_at,
            complaints.c.created_at,
        )
    ).mappings().all()
    for row in rows:
        values = {
            "complaint_no": f"CPLEGACY{row['id']:012d}",
            "category": "other",
            "updated_at": row["created_at"],
        }
        if row["status"] == "viewed":
            values["status"] = "processing"
            values["processing_started_at"] = row["viewed_at"]
        bind.execute(complaints.update().where(complaints.c.id == row["id"]).values(**values))

    op.alter_column("complaints", "complaint_no", existing_type=sa.String(length=64), nullable=False)
    op.alter_column(
        "complaints",
        "category",
        existing_type=sa.String(length=32),
        nullable=False,
        server_default="other",
    )
    op.alter_column(
        "complaints",
        "updated_at",
        existing_type=sa.DateTime(),
        nullable=False,
        server_default=sa.func.now(),
    )
    op.create_unique_constraint("uq_complaints_complaint_no", "complaints", ["complaint_no"])
    op.create_index(
        "ix_complaints_submitter_created",
        "complaints",
        ["submitter_user_id", "created_at", "id"],
    )
    op.create_index(
        "ix_complaints_category_status_created",
        "complaints",
        ["category", "status", "created_at", "id"],
    )


def downgrade():
    op.drop_index("ix_complaints_category_status_created", table_name="complaints")
    op.drop_index("ix_complaints_submitter_created", table_name="complaints")
    op.drop_constraint("uq_complaints_complaint_no", "complaints", type_="unique")
    op.drop_constraint("fk_complaints_handled_by_users", "complaints", type_="foreignkey")
    op.drop_column("complaints", "updated_at")
    op.drop_column("complaints", "handled_at")
    op.drop_column("complaints", "handling_opinion")
    op.drop_column("complaints", "handling_result")
    op.drop_column("complaints", "handled_by")
    op.drop_column("complaints", "processing_started_at")
    op.drop_column("complaints", "category")
    op.drop_column("complaints", "complaint_no")
