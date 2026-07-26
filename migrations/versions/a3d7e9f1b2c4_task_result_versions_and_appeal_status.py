"""task result versions and appeal lifecycle status

Revision ID: a3d7e9f1b2c4
Revises: f2c8d4a7b9e1
Create Date: 2026-07-24 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "a3d7e9f1b2c4"
down_revision = "f2c8d4a7b9e1"
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    if not sa.inspect(bind).has_table("task_result_submission_versions"):
        op.create_table(
            "task_result_submission_versions",
            sa.Column("id", sa.BigInteger(), nullable=False),
            sa.Column("submission_id", sa.BigInteger(), nullable=False),
            sa.Column("version_no", sa.Integer(), nullable=False),
            sa.Column("summary", sa.Text(), nullable=False),
            sa.Column("requested_hours", sa.Numeric(10, 2), nullable=False),
            sa.Column("attachment_ids", sa.JSON(), nullable=False),
            sa.Column("submitted_by", sa.BigInteger(), nullable=False),
            sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
            sa.ForeignKeyConstraint(["submission_id"], ["task_result_submissions.id"]),
            sa.ForeignKeyConstraint(["submitted_by"], ["users.id"]),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint(
                "submission_id",
                "version_no",
                name="uq_task_result_submission_version",
            ),
        )

    metadata = sa.MetaData()
    submissions = sa.Table(
        "task_result_submissions",
        metadata,
        sa.Column("id", sa.BigInteger()),
        sa.Column("leader_student_id", sa.BigInteger()),
        sa.Column("summary", sa.Text()),
        sa.Column("requested_hours", sa.Numeric(10, 2)),
        sa.Column("created_at", sa.DateTime()),
    )
    students = sa.Table(
        "students",
        metadata,
        sa.Column("id", sa.BigInteger()),
        sa.Column("user_id", sa.BigInteger()),
    )
    versions = sa.Table(
        "task_result_submission_versions",
        metadata,
        sa.Column("submission_id", sa.BigInteger()),
        sa.Column("version_no", sa.Integer()),
        sa.Column("summary", sa.Text()),
        sa.Column("requested_hours", sa.Numeric(10, 2)),
        sa.Column("attachment_ids", sa.JSON()),
        sa.Column("submitted_by", sa.BigInteger()),
        sa.Column("created_at", sa.DateTime()),
    )
    existing_version_select = (
        sa.select(
            submissions.c.id,
            sa.literal(1),
            submissions.c.summary,
            submissions.c.requested_hours,
            sa.literal([], type_=sa.JSON()),
            students.c.user_id,
            submissions.c.created_at,
        )
        .select_from(
            submissions.join(
                students,
                students.c.id == submissions.c.leader_student_id,
            )
        )
        .where(
            ~sa.exists().where(
                versions.c.submission_id == submissions.c.id
            )
        )
    )
    bind.execute(
        versions.insert().from_select(
            [
                "submission_id",
                "version_no",
                "summary",
                "requested_hours",
                "attachment_ids",
                "submitted_by",
                "created_at",
            ],
            existing_version_select,
        )
    )
    op.execute(
        "UPDATE appeals SET status = 'processing' "
        "WHERE status = 'appeal_accepted'"
    )
    op.execute(
        "UPDATE appeals SET status = 'completed' "
        "WHERE status = 'appeal_rejected'"
    )


def downgrade():
    op.execute(
        "UPDATE appeals SET status = 'appeal_accepted' "
        "WHERE status = 'processing'"
    )
    op.execute(
        "UPDATE appeals SET status = 'appeal_rejected' "
        "WHERE status = 'completed' AND admin_decision = 'maintain'"
    )
    op.execute(
        "UPDATE appeals SET status = 'appeal_accepted' "
        "WHERE status = 'completed'"
    )
    op.drop_table("task_result_submission_versions")
