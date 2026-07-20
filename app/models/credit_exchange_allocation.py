from sqlalchemy.orm import relationship

from app.extensions import db


class CreditExchangeAllocation(db.Model):
    __tablename__ = "credit_exchange_allocations"

    id = db.Column(db.BigInteger, primary_key=True)
    exchange_application_id = db.Column(
        db.BigInteger,
        db.ForeignKey("credit_exchange_applications.id"),
        nullable=False,
    )
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    allocated_hours = db.Column(db.Numeric(10, 2), nullable=False)
    credit_type = db.Column(db.String(64), nullable=False, default="innovation_credit")
    allocated_credits = db.Column(db.Numeric(10, 2), nullable=False)
    remark = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    student = relationship("Student", lazy="joined")
