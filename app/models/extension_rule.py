from sqlalchemy.orm import relationship

from app.extensions import db


class ExtensionRule(db.Model):
    __tablename__ = "extension_rules"
    __table_args__ = (
        db.Index("ix_extension_rules_status_effective", "status", "effective_at", "id"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    rule_name = db.Column(db.String(128), nullable=False)
    ordinary_max_days = db.Column(db.Integer, nullable=False)
    special_threshold_days = db.Column(db.Integer, nullable=False)
    special_max_days = db.Column(db.Integer, nullable=False)
    max_extension_requests = db.Column(db.Integer, nullable=False)
    default_material_due_days = db.Column(db.Integer, nullable=False)
    allow_beyond_graduation = db.Column(db.Boolean, nullable=False, default=True)
    effective_at = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="enabled")
    version = db.Column(db.Integer, nullable=False, default=1)
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    updated_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    task_type_links = relationship(
        "ExtensionRuleTaskType",
        cascade="all, delete-orphan",
        lazy="select",
        back_populates="rule",
    )
    creator = relationship("User", foreign_keys=[created_by], lazy="joined")
    updater = relationship("User", foreign_keys=[updated_by], lazy="joined")

    @property
    def task_types(self):
        return [link.task_type for link in self.task_type_links]
