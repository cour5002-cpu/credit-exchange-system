"""week3 hour application mainline

Revision ID: 7b3d3f2e9a1c
Revises: 2d2b0a7c9e11
Create Date: 2026-07-14 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7b3d3f2e9a1c"
down_revision = "2d2b0a7c9e11"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("hour_applications", schema=None) as batch_op:
        batch_op.add_column(sa.Column("applicant_student_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("leader_student_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("application_type", sa.String(length=32), nullable=False, server_default="with_material"))
        batch_op.add_column(sa.Column("source_type", sa.String(length=32), nullable=False, server_default="student_self"))
        batch_op.add_column(sa.Column("source_task_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("task_result_submission_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("task_type_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("reviewer_suggested_hours", sa.Numeric(10, 2), nullable=True))
        batch_op.add_column(sa.Column("achievement_summary", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("material_due_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("extension_count", sa.Integer(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("appeal_advice", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("appeal_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("submitted_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("advisor_reviewed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("reviewer_reviewed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("final_reviewed_at", sa.DateTime(), nullable=True))
        batch_op.alter_column("status", existing_type=sa.String(length=20), type_=sa.String(length=32), existing_nullable=False)
        batch_op.create_foreign_key("fk_hour_applications_applicant_student_id_students", "students", ["applicant_student_id"], ["id"])
        batch_op.create_foreign_key("fk_hour_applications_leader_student_id_students", "students", ["leader_student_id"], ["id"])
        batch_op.create_foreign_key("fk_hour_applications_task_type_id_task_types", "task_types", ["task_type_id"], ["id"])

    with op.batch_alter_table("hour_application_reviews", schema=None) as batch_op:
        batch_op.add_column(sa.Column("operator_user_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("operator_teacher_id", sa.BigInteger(), nullable=True))
        batch_op.add_column(sa.Column("stage", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("operator_role", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("decision", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("before_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("after_status", sa.String(length=32), nullable=True))
        batch_op.add_column(sa.Column("requested_hours_snapshot", sa.Numeric(10, 2), nullable=True))
        batch_op.alter_column("reviewer_teacher_id", existing_type=sa.BigInteger(), nullable=True)
        batch_op.create_foreign_key("fk_hour_application_reviews_operator_user_id_users", "users", ["operator_user_id"], ["id"])
        batch_op.create_foreign_key("fk_hour_application_reviews_operator_teacher_id_teachers", "teachers", ["operator_teacher_id"], ["id"])

    op.create_table(
        "hour_application_members",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("hour_applications.id"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("is_leader", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("can_view", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("can_apply_credit_exchange", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("joined_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "application_advisors",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("hour_applications.id"), nullable=False),
        sa.Column("teacher_id", sa.BigInteger(), sa.ForeignKey("teachers.id"), nullable=False),
        sa.Column("advisor_role", sa.String(length=20), nullable=False, server_default="primary"),
        sa.Column("can_operate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "review_assignments",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("hour_applications.id"), nullable=False),
        sa.Column("reviewer_teacher_id", sa.BigInteger(), sa.ForeignKey("teachers.id"), nullable=False),
        sa.Column("assigned_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("assign_reason", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("assigned_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "hour_award_records",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("application_id", sa.BigInteger(), sa.ForeignKey("hour_applications.id"), nullable=False, unique=True),
        sa.Column("leader_student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("total_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("awarded_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("awarded_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("is_exchanged", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("remark", sa.String(length=255), nullable=True),
    )


def downgrade():
    op.drop_table("hour_award_records")
    op.drop_table("review_assignments")
    op.drop_table("application_advisors")
    op.drop_table("hour_application_members")

    with op.batch_alter_table("hour_application_reviews", schema=None) as batch_op:
        batch_op.drop_constraint("fk_hour_application_reviews_operator_teacher_id_teachers", type_="foreignkey")
        batch_op.drop_constraint("fk_hour_application_reviews_operator_user_id_users", type_="foreignkey")
        batch_op.alter_column("reviewer_teacher_id", existing_type=sa.BigInteger(), nullable=False)
        batch_op.drop_column("requested_hours_snapshot")
        batch_op.drop_column("after_status")
        batch_op.drop_column("before_status")
        batch_op.drop_column("decision")
        batch_op.drop_column("operator_role")
        batch_op.drop_column("stage")
        batch_op.drop_column("operator_teacher_id")
        batch_op.drop_column("operator_user_id")

    with op.batch_alter_table("hour_applications", schema=None) as batch_op:
        batch_op.drop_constraint("fk_hour_applications_task_type_id_task_types", type_="foreignkey")
        batch_op.drop_constraint("fk_hour_applications_leader_student_id_students", type_="foreignkey")
        batch_op.drop_constraint("fk_hour_applications_applicant_student_id_students", type_="foreignkey")
        batch_op.alter_column("status", existing_type=sa.String(length=32), type_=sa.String(length=20), existing_nullable=False)
        batch_op.drop_column("final_reviewed_at")
        batch_op.drop_column("reviewer_reviewed_at")
        batch_op.drop_column("advisor_reviewed_at")
        batch_op.drop_column("submitted_at")
        batch_op.drop_column("appeal_id")
        batch_op.drop_column("appeal_advice")
        batch_op.drop_column("extension_count")
        batch_op.drop_column("material_due_at")
        batch_op.drop_column("achievement_summary")
        batch_op.drop_column("reviewer_suggested_hours")
        batch_op.drop_column("task_type_id")
        batch_op.drop_column("task_result_submission_id")
        batch_op.drop_column("source_task_id")
        batch_op.drop_column("source_type")
        batch_op.drop_column("application_type")
        batch_op.drop_column("leader_student_id")
        batch_op.drop_column("applicant_student_id")
