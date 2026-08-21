from sqlalchemy.orm import relationship

from app.extensions import db


class Appeal(db.Model):
    __tablename__ = "appeals"
    __table_args__ = (
        db.Index("ix_appeals_target", "target_type", "target_id"),
        db.Index("ix_appeals_status_stage_created", "status", "reopen_stage", "created_at", "id"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    appeal_no = db.Column(db.String(64), unique=True, nullable=False)
    target_type = db.Column(db.String(64), nullable=False)
    target_id = db.Column(db.BigInteger, nullable=False)
    applicant_student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending_admin_review")
    admin_decision = db.Column(db.String(32))
    admin_advice = db.Column(db.Text)
    original_status = db.Column(db.String(32))
    reopen_stage = db.Column(db.String(32))
    standard_rule_file_id = db.Column(db.BigInteger, db.ForeignKey("rule_files.id"))
    reviewed_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    reviewed_at = db.Column(db.DateTime)
    reconfirmed_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    reconfirmed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    applicant = relationship("Student", lazy="joined")
    standard_rule_file = relationship("RuleFile", lazy="joined")
