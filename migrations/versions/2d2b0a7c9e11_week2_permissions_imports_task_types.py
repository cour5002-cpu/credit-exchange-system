"""week2 permissions imports task types

Revision ID: 2d2b0a7c9e11
Revises: ac4b6114128d
Create Date: 2026-07-12 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "2d2b0a7c9e11"
down_revision = "ac4b6114128d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("students", schema=None) as batch_op:
        batch_op.add_column(sa.Column("import_batch_no", sa.String(length=64), nullable=True))

    with op.batch_alter_table("teachers", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "role_flags",
                sa.String(length=128),
                nullable=False,
                server_default="advisor,reviewer",
            )
        )

    with op.batch_alter_table("task_types", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("allow_student_self", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch_op.add_column(
            sa.Column("allow_admin_task", sa.Boolean(), nullable=False, server_default=sa.true())
        )
        batch_op.add_column(
            sa.Column("allow_teacher_task", sa.Boolean(), nullable=False, server_default=sa.true())
        )


def downgrade():
    with op.batch_alter_table("task_types", schema=None) as batch_op:
        batch_op.drop_column("allow_teacher_task")
        batch_op.drop_column("allow_admin_task")
        batch_op.drop_column("allow_student_self")

    with op.batch_alter_table("teachers", schema=None) as batch_op:
        batch_op.drop_column("role_flags")

    with op.batch_alter_table("students", schema=None) as batch_op:
        batch_op.drop_column("import_batch_no")
