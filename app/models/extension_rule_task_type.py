from sqlalchemy.orm import relationship

from app.extensions import db


class ExtensionRuleTaskType(db.Model):
    __tablename__ = "extension_rule_task_types"
    __table_args__ = (
        db.UniqueConstraint("rule_id", "task_type_id", name="uq_extension_rule_task_type"),
        db.Index("ix_extension_rule_types_task_rule", "task_type_id", "rule_id"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    rule_id = db.Column(
        db.BigInteger,
        db.ForeignKey("extension_rules.id", ondelete="CASCADE"),
        nullable=False,
    )
    task_type_id = db.Column(db.BigInteger, db.ForeignKey("task_types.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    rule = relationship("ExtensionRule", back_populates="task_type_links")
    task_type = relationship("TaskType", lazy="joined")
