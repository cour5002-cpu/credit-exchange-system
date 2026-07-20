"""week5 appeals and college tasks

Revision ID: b7e6c9d2a5f1
Revises: f4a1c2b3d4e5
Create Date: 2026-07-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b7e6c9d2a5f1"
down_revision = "f4a1c2b3d4e5"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if "appeals" not in tables:
        op.create_table(
            "appeals",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("appeal_no", sa.String(length=64), nullable=False, unique=True),
            sa.Column("target_type", sa.String(length=64), nullable=False),
            sa.Column("target_id", sa.BigInteger(), nullable=False),
            sa.Column("applicant_student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
            sa.Column("reason", sa.Text(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="pending_admin_review"),
            sa.Column("admin_decision", sa.String(length=32), nullable=True),
            sa.Column("admin_advice", sa.Text(), nullable=True),
            sa.Column("standard_rule_file_id", sa.BigInteger(), sa.ForeignKey("rule_files.id"), nullable=True),
            sa.Column("reviewed_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("reviewed_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
    _create_index_if_missing(inspector, "appeals", "ix_appeals_target", ["target_type", "target_id"], unique=False)

    if "college_tasks" not in tables:
        op.create_table(
            "college_tasks",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("task_no", sa.String(length=64), nullable=False, unique=True),
            sa.Column("title", sa.String(length=255), nullable=False),
            sa.Column("description", sa.Text(), nullable=False),
            sa.Column("task_type_id", sa.BigInteger(), sa.ForeignKey("task_types.id"), nullable=False),
            sa.Column("major_name", sa.String(length=128), nullable=False),
            sa.Column("course_name", sa.String(length=128), nullable=False),
            sa.Column("requirement", sa.Text(), nullable=False),
            sa.Column("publisher_type", sa.String(length=20), nullable=False),
            sa.Column("publisher_user_id", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("advisor_teacher_id", sa.BigInteger(), sa.ForeignKey("teachers.id"), nullable=False),
            sa.Column("registration_start_at", sa.DateTime(), nullable=True),
            sa.Column("registration_deadline", sa.DateTime(), nullable=False),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
            sa.Column("admin_reviewed_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("admin_review_comment", sa.Text(), nullable=True),
            sa.Column("published_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )

    if "task_registrations" not in tables:
        op.create_table(
            "task_registrations",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("college_tasks.id"), nullable=False),
            sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
            sa.Column("apply_reason", sa.Text(), nullable=True),
            sa.Column("status", sa.String(length=32), nullable=False, server_default="submitted"),
            sa.Column("selected_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=True),
            sa.Column("selected_at", sa.DateTime(), nullable=True),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
            sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
    _create_index_if_missing(inspector, "task_registrations", "uq_task_registration_student", ["task_id", "student_id"], unique=True)

    if "task_members" not in tables:
        op.create_table(
            "task_members",
            sa.Column("id", sa.BigInteger(), primary_key=True),
            sa.Column("task_id", sa.BigInteger(), sa.ForeignKey("college_tasks.id"), nullable=False),
            sa.Column("registration_id", sa.BigInteger(), sa.ForeignKey("task_registrations.id"), nullable=True),
            sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
            sa.Column("is_leader", sa.Boolean(), nullable=False, server_default=sa.false()),
            sa.Column("selected_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
            sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
            sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        )
    _create_index_if_missing(inspector, "task_members", "uq_task_member_student", ["task_id", "student_id"], unique=True)


def downgrade():
    op.drop_index("uq_task_member_student", table_name="task_members")
    op.drop_table("task_members")
    op.drop_index("uq_task_registration_student", table_name="task_registrations")
    op.drop_table("task_registrations")
    op.drop_table("college_tasks")
    op.drop_index("ix_appeals_target", table_name="appeals")
    op.drop_table("appeals")


def _create_index_if_missing(inspector, table_name, index_name, columns, unique):
    index_names = {item["name"] for item in inspector.get_indexes(table_name)}
    if index_name not in index_names:
        op.create_index(index_name, table_name, columns, unique=unique)
