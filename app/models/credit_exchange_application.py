from sqlalchemy.orm import relationship

from app.extensions import db


class CreditExchangeApplication(db.Model):
    __tablename__ = "credit_exchange_applications"
    __table_args__ = (
        db.Index("ix_credit_exchanges_status_created", "status", "created_at", "id"),
    )

    STATUS_LABELS = {
        "draft": "草稿",
        "submitted": "待审核",
        "advisor_approved": "指导老师已确认",
        "advisor_rejected": "指导老师已驳回",
        "pending_admin_final": "待管理员最终确认",
        "final_approved": "最终通过",
        "final_rejected": "最终驳回",
        "approved": "已通过",
        "rejected": "已驳回",
    }

    id = db.Column(db.BigInteger, primary_key=True)
    exchange_no = db.Column(db.String(64), unique=True, nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    requested_hours = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_credits = db.Column(db.Numeric(10, 2))
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="submitted")
    reviewed_by_admin_id = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    review_comment = db.Column(db.Text)
    approved_at = db.Column(db.DateTime)
    hour_application_id = db.Column(db.BigInteger, db.ForeignKey("hour_applications.id"))
    hour_award_record_id = db.Column(db.BigInteger, db.ForeignKey("hour_award_records.id"))
    applicant_student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"))
    advisor_teacher_id = db.Column(db.BigInteger, db.ForeignKey("teachers.id"))
    total_hours = db.Column(db.Numeric(10, 2))
    estimated_total_credits = db.Column(db.Numeric(10, 2))
    rule_id = db.Column(db.BigInteger, db.ForeignKey("credit_conversion_rules.id"))
    rule_snapshot = db.Column(db.JSON)
    advisor_reviewed_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    advisor_review_comment = db.Column(db.Text)
    advisor_reviewed_at = db.Column(db.DateTime)
    admin_reviewed_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    admin_review_comment = db.Column(db.Text)
    admin_reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    student = relationship("Student", foreign_keys=[student_id], lazy="joined")
    applicant = relationship("Student", foreign_keys=[applicant_student_id], lazy="joined")
    hour_application = relationship("HourApplication", lazy="joined")
    hour_award_record = relationship("HourAwardRecord", lazy="joined")
    advisor = relationship("Teacher", lazy="joined")
    conversion_rule = relationship("CreditConversionRule", lazy="joined")
    allocations = relationship(
        "CreditExchangeAllocation",
        cascade="all, delete-orphan",
        lazy="select",
        backref="exchange_application",
    )

    @property
    def status_name(self):
        return self.STATUS_LABELS.get(self.status, self.status)
