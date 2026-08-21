"""add v3 extension rules and snapshots

Revision ID: a0b1c2d3e4f5
Revises: f9a0b1c2d3e4
Create Date: 2026-08-10 10:10:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "a0b1c2d3e4f5"
down_revision = "f9a0b1c2d3e4"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "extension_rules",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column("rule_name", sa.String(length=128), nullable=False),
        sa.Column("ordinary_max_days", sa.Integer(), nullable=False),
        sa.Column("special_threshold_days", sa.Integer(), nullable=False),
        sa.Column("special_max_days", sa.Integer(), nullable=False),
        sa.Column("max_extension_requests", sa.Integer(), nullable=False),
        sa.Column("default_material_due_days", sa.Integer(), nullable=False),
        sa.Column("allow_beyond_graduation", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("effective_at", sa.DateTime(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="enabled"),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("updated_by", sa.BigInteger(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(
        "ix_extension_rules_status_effective",
        "extension_rules",
        ["status", "effective_at", "id"],
    )
    op.create_table(
        "extension_rule_task_types",
        sa.Column("id", sa.BigInteger(), primary_key=True),
        sa.Column(
            "rule_id",
            sa.BigInteger(),
            sa.ForeignKey("extension_rules.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("task_type_id", sa.BigInteger(), sa.ForeignKey("task_types.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("rule_id", "task_type_id", name="uq_extension_rule_task_type"),
    )
    op.create_index(
        "ix_extension_rule_types_task_rule",
        "extension_rule_task_types",
        ["task_type_id", "rule_id"],
    )

    op.add_column("students", sa.Column("expected_graduation_date", sa.Date(), nullable=True))
    op.add_column("extension_requests", sa.Column("rule_id", sa.BigInteger(), nullable=True))
    op.add_column("extension_requests", sa.Column("rule_snapshot", sa.JSON(), nullable=True))
    op.add_column("extension_requests", sa.Column("submitted_at", sa.DateTime(), nullable=True))
    op.add_column(
        "extension_requests",
        sa.Column("approved_extension_days_before", sa.Integer(), nullable=True),
    )
    op.add_column(
        "extension_requests",
        sa.Column("projected_total_extension_days", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_extension_requests_rule_id",
        "extension_requests",
        "extension_rules",
        ["rule_id"],
        ["id"],
    )

    bind = op.get_bind()
    extensions = sa.table(
        "extension_requests",
        sa.column("id", sa.BigInteger()),
        sa.column("extension_days", sa.Integer()),
        sa.column("created_at", sa.DateTime()),
        sa.column("submitted_at", sa.DateTime()),
        sa.column("rule_snapshot", sa.JSON()),
        sa.column("approved_extension_days_before", sa.Integer()),
        sa.column("projected_total_extension_days", sa.Integer()),
    )
    rows = bind.execute(
        sa.select(extensions.c.id, extensions.c.extension_days, extensions.c.created_at)
    ).mappings().all()
    for row in rows:
        bind.execute(
            extensions.update().where(extensions.c.id == row["id"]).values(
                submitted_at=row["created_at"],
                rule_snapshot={
                    "schema_version": 0,
                    "legacy": True,
                    "special_threshold_days": 30,
                },
                approved_extension_days_before=0,
                projected_total_extension_days=row["extension_days"] or 0,
            )
        )

    op.alter_column(
        "extension_requests",
        "approved_extension_days_before",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="0",
    )
    op.alter_column(
        "extension_requests",
        "projected_total_extension_days",
        existing_type=sa.Integer(),
        nullable=False,
        server_default="0",
    )

    _drop_application_unique()
    op.create_index(
        "ix_extension_requests_application_created",
        "extension_requests",
        ["application_id", "created_at", "id"],
    )
    op.create_index(
        "ix_extension_requests_application_status",
        "extension_requests",
        ["application_id", "status", "id"],
    )
    op.create_index("ix_extension_requests_rule", "extension_requests", ["rule_id"])
    op.execute(
        "UPDATE hour_applications h SET extension_count = "
        "(SELECT COUNT(*) FROM extension_requests e WHERE e.application_id = h.id)"
    )
    op.execute(
        "UPDATE system_configs SET description = "
        "'deprecated：V3改用extension_rules' "
        "WHERE config_key = 'extension_special_threshold_days'"
    )


def downgrade():
    bind = op.get_bind()
    duplicates = bind.execute(sa.text(
        "SELECT application_id FROM extension_requests GROUP BY application_id HAVING COUNT(*) > 1 LIMIT 1"
    )).first()
    if duplicates:
        raise RuntimeError("存在同一课时申请的多条延期记录，不能安全恢复唯一约束")
    op.drop_index("ix_extension_requests_rule", table_name="extension_requests")
    op.drop_index("ix_extension_requests_application_status", table_name="extension_requests")
    op.drop_index("ix_extension_requests_application_created", table_name="extension_requests")
    op.create_unique_constraint(
        "uq_extension_requests_application_id",
        "extension_requests",
        ["application_id"],
    )
    if any(
        index.get("name") == "ix_extension_requests_application_id_fk"
        for index in sa.inspect(bind).get_indexes("extension_requests")
    ):
        op.drop_index("ix_extension_requests_application_id_fk", table_name="extension_requests")
    op.drop_constraint("fk_extension_requests_rule_id", "extension_requests", type_="foreignkey")
    op.drop_column("extension_requests", "projected_total_extension_days")
    op.drop_column("extension_requests", "approved_extension_days_before")
    op.drop_column("extension_requests", "submitted_at")
    op.drop_column("extension_requests", "rule_snapshot")
    op.drop_column("extension_requests", "rule_id")
    op.drop_column("students", "expected_graduation_date")
    op.drop_index("ix_extension_rule_types_task_rule", table_name="extension_rule_task_types")
    op.drop_table("extension_rule_task_types")
    op.drop_index("ix_extension_rules_status_effective", table_name="extension_rules")
    op.drop_table("extension_rules")


def _drop_application_unique():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    indexes = inspector.get_indexes("extension_requests")
    # MySQL may reuse the unique application_id index for the foreign key. A
    # normal supporting index must exist before uniqueness can be removed.
    if bind.dialect.name == "mysql" and not any(
        index.get("column_names") == ["application_id"] and not index.get("unique")
        for index in indexes
    ):
        op.create_index(
            "ix_extension_requests_application_id_fk",
            "extension_requests",
            ["application_id"],
        )
        inspector = sa.inspect(bind)
    for constraint in inspector.get_unique_constraints("extension_requests"):
        if constraint.get("column_names") == ["application_id"]:
            op.drop_constraint(constraint["name"], "extension_requests", type_="unique")
            return
    for index in inspector.get_indexes("extension_requests"):
        if index.get("unique") and index.get("column_names") == ["application_id"]:
            op.drop_index(index["name"], table_name="extension_requests")
            return
    raise RuntimeError("未找到 extension_requests.application_id 唯一约束")
