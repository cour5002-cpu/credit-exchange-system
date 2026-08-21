"""week4 credit exchange mainline

Revision ID: f4a1c2b3d4e5
Revises: 9c4e1a7b2d6f
Create Date: 2026-07-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "f4a1c2b3d4e5"
down_revision = "9c4e1a7b2d6f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "rule_files",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("rule_type", sa.String(length=64), nullable=False),
        sa.Column("usage_type", sa.String(length=32), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("attachment_id", sa.BigInteger(), sa.ForeignKey("attachments.id"), nullable=False),
        sa.Column("version_no", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("uploaded_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "credit_conversion_rules",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("rule_name", sa.String(length=128), nullable=False),
        sa.Column("hours_per_credit", sa.Numeric(10, 2), nullable=False),
        sa.Column("max_single_exchange_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("rounding_mode", sa.String(length=32), nullable=False),
        sa.Column("effective_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("rule_file_id", sa.BigInteger(), sa.ForeignKey("rule_files.id"), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "credit_exchange_allocations",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("exchange_application_id", sa.BigInteger(), sa.ForeignKey("credit_exchange_applications.id"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("allocated_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("credit_type", sa.String(length=64), nullable=False, server_default="innovation_credit"),
        sa.Column("allocated_credits", sa.Numeric(10, 2), nullable=False),
        sa.Column("remark", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "student_credit_records",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("exchange_record_id", sa.BigInteger(), sa.ForeignKey("credit_exchange_records.id"), nullable=False),
        sa.Column("exchange_application_id", sa.BigInteger(), sa.ForeignKey("credit_exchange_applications.id"), nullable=False),
        sa.Column("student_id", sa.BigInteger(), sa.ForeignKey("students.id"), nullable=False),
        sa.Column("credit_type", sa.String(length=64), nullable=False),
        sa.Column("credits", sa.Numeric(10, 2), nullable=False),
        sa.Column("source_hours", sa.Numeric(10, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    with op.batch_alter_table("credit_exchange_applications") as batch:
        batch.add_column(sa.Column("hour_application_id", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("hour_award_record_id", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("applicant_student_id", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("advisor_teacher_id", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("total_hours", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("estimated_total_credits", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("rule_id", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("rule_snapshot", sa.JSON(), nullable=True))
        batch.add_column(sa.Column("advisor_reviewed_by", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("advisor_review_comment", sa.Text(), nullable=True))
        batch.add_column(sa.Column("advisor_reviewed_at", sa.DateTime(), nullable=True))
        batch.add_column(sa.Column("admin_reviewed_by", sa.BigInteger(), nullable=True))
        batch.add_column(sa.Column("admin_review_comment", sa.Text(), nullable=True))
        batch.add_column(sa.Column("admin_reviewed_at", sa.DateTime(), nullable=True))
        batch.create_foreign_key("fk_credit_exchange_hour_application", "hour_applications", ["hour_application_id"], ["id"])
        batch.create_foreign_key("fk_credit_exchange_hour_award", "hour_award_records", ["hour_award_record_id"], ["id"])
        batch.create_foreign_key("fk_credit_exchange_applicant", "students", ["applicant_student_id"], ["id"])
        batch.create_foreign_key("fk_credit_exchange_advisor", "teachers", ["advisor_teacher_id"], ["id"])
        batch.create_foreign_key("fk_credit_exchange_rule", "credit_conversion_rules", ["rule_id"], ["id"])
        batch.create_foreign_key("fk_credit_exchange_advisor_user", "users", ["advisor_reviewed_by"], ["id"])
        batch.create_foreign_key("fk_credit_exchange_admin_user", "users", ["admin_reviewed_by"], ["id"])
    with op.batch_alter_table("credit_exchange_records") as batch:
        batch.add_column(sa.Column("total_used_hours", sa.Numeric(10, 2), nullable=True))
        batch.add_column(sa.Column("total_credits", sa.Numeric(10, 2), nullable=True))


def downgrade():
    with op.batch_alter_table("credit_exchange_records") as batch:
        batch.drop_column("total_credits")
        batch.drop_column("total_used_hours")
    with op.batch_alter_table("credit_exchange_applications") as batch:
        batch.drop_constraint("fk_credit_exchange_admin_user", type_="foreignkey")
        batch.drop_constraint("fk_credit_exchange_advisor_user", type_="foreignkey")
        batch.drop_constraint("fk_credit_exchange_rule", type_="foreignkey")
        batch.drop_constraint("fk_credit_exchange_advisor", type_="foreignkey")
        batch.drop_constraint("fk_credit_exchange_applicant", type_="foreignkey")
        batch.drop_constraint("fk_credit_exchange_hour_award", type_="foreignkey")
        batch.drop_constraint("fk_credit_exchange_hour_application", type_="foreignkey")
        batch.drop_column("admin_reviewed_at")
        batch.drop_column("admin_review_comment")
        batch.drop_column("admin_reviewed_by")
        batch.drop_column("advisor_reviewed_at")
        batch.drop_column("advisor_review_comment")
        batch.drop_column("advisor_reviewed_by")
        batch.drop_column("rule_snapshot")
        batch.drop_column("rule_id")
        batch.drop_column("estimated_total_credits")
        batch.drop_column("total_hours")
        batch.drop_column("advisor_teacher_id")
        batch.drop_column("applicant_student_id")
        batch.drop_column("hour_award_record_id")
        batch.drop_column("hour_application_id")
    op.drop_table("student_credit_records")
    op.drop_table("credit_exchange_allocations")
    op.drop_table("credit_conversion_rules")
    op.drop_table("rule_files")
