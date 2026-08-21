from sqlalchemy.orm import relationship

from app.extensions import db


class ExtensionRequest(db.Model):
    __tablename__ = "extension_requests"
    __table_args__ = (
        db.Index("ix_extension_requests_level_status_created", "review_level", "status", "created_at", "id"),
        db.Index("ix_extension_requests_application_created", "application_id", "created_at", "id"),
        db.Index("ix_extension_requests_application_status", "application_id", "status", "id"),
        db.Index("ix_extension_requests_rule", "rule_id"),
        db.Index("ix_extension_requests_application_id_fk", "application_id"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    application_id = db.Column(
        db.BigInteger,
        db.ForeignKey("hour_applications.id"),
        nullable=False,
    )
    old_due_at = db.Column(db.DateTime, nullable=False)
    requested_due_at = db.Column(db.DateTime, nullable=False)
    extension_days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    review_level = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending_advisor_review")
    reviewed_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    review_comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    reviewed_at = db.Column(db.DateTime)
    rule_id = db.Column(db.BigInteger, db.ForeignKey("extension_rules.id"))
    rule_snapshot = db.Column(db.JSON)
    submitted_at = db.Column(db.DateTime)
    approved_extension_days_before = db.Column(db.Integer, nullable=False, default=0)
    projected_total_extension_days = db.Column(db.Integer, nullable=False, default=0)

    application = relationship("HourApplication", backref="extension_requests")
    reviewer = relationship("User", lazy="joined")
    rule = relationship("ExtensionRule", lazy="joined")
