"""complete week5 v1 flows

Revision ID: e9a4b2c7d1f6
Revises: d8f3a1c6e2b4
Create Date: 2026-07-20 20:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "e9a4b2c7d1f6"
down_revision = "d8f3a1c6e2b4"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    appeal_columns = {item["name"] for item in inspector.get_columns("appeals")}
    appeal_foreign_keys = {item.get("name") for item in inspector.get_foreign_keys("appeals")}
    with op.batch_alter_table("appeals") as batch_op:
        if "original_status" not in appeal_columns:
            batch_op.add_column(sa.Column("original_status", sa.String(length=32), nullable=True))
        if "reopen_stage" not in appeal_columns:
            batch_op.add_column(sa.Column("reopen_stage", sa.String(length=32), nullable=True))
        if "reconfirmed_by" not in appeal_columns:
            batch_op.add_column(sa.Column("reconfirmed_by", sa.BigInteger(), nullable=True))
        if "reconfirmed_at" not in appeal_columns:
            batch_op.add_column(sa.Column("reconfirmed_at", sa.DateTime(), nullable=True))
        if "fk_appeals_reconfirmed_by_users" not in appeal_foreign_keys:
            batch_op.create_foreign_key("fk_appeals_reconfirmed_by_users", "users", ["reconfirmed_by"], ["id"])

    tables = set(sa.inspect(bind).get_table_names())
    if "task_result_submissions" not in tables:
        op.create_table(
            "task_result_submissions",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("college_tasks.id"), nullable=False),
        sa.Column("leader_student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("requested_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="submitted"),
        sa.Column("hour_application_id", sa.BigInteger(), sa.ForeignKey("hour_applications.id"), nullable=True),
        sa.Column("advisor_comment", sa.Text(), nullable=True),
        sa.Column("advisor_reviewed_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("advisor_reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
    inspector = sa.inspect(bind)
    result_indexes = {item["name"] for item in inspector.get_indexes("task_result_submissions")}
    if "uq_task_result_submission_task" not in result_indexes:
        op.create_index("uq_task_result_submission_task", "task_result_submissions", ["task_id"], unique=True)

    if "complaints" not in tables:
        op.create_table(
            "complaints",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("submitter_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="submitted"),
        sa.Column("viewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )


def downgrade():
    op.drop_table("complaints")
    op.drop_index("uq_task_result_submission_task", table_name="task_result_submissions")
    op.drop_table("task_result_submissions")
    with op.batch_alter_table("appeals") as batch_op:
        batch_op.drop_constraint("fk_appeals_reconfirmed_by_users", type_="foreignkey")
        batch_op.drop_column("reconfirmed_at")
        batch_op.drop_column("reconfirmed_by")
        batch_op.drop_column("reopen_stage")
        batch_op.drop_column("original_status")
