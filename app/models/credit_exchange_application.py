from sqlalchemy.orm import relationship

from app.extensions import db


class CreditExchangeApplication(db.Model):
    __tablename__ = "credit_exchange_applications"

    STATUS_LABELS = {
        "submitted": "待审核",
        "approved": "已通过",
        "rejected": "已驳回",
    }

    id = db.Column(db.BigInteger, primary_key=True)
    exchange_no = db.Column(db.String(64), unique=True, nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    requested_hours = db.Column(db.Numeric(10, 2), nullable=False)
    estimated_credits = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="submitted")
    reviewed_by_admin_id = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    review_comment = db.Column(db.Text)
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    student = relationship("Student", lazy="joined")

    @property
    def status_name(self):
        return self.STATUS_LABELS.get(self.status, self.status)
