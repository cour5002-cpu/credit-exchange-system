from sqlalchemy.orm import relationship

from app.extensions import db


class StudentCreditRecord(db.Model):
    __tablename__ = "student_credit_records"

    id = db.Column(db.BigInteger, primary_key=True)
    exchange_record_id = db.Column(db.BigInteger, db.ForeignKey("credit_exchange_records.id"), nullable=False)
    exchange_application_id = db.Column(db.BigInteger, db.ForeignKey("credit_exchange_applications.id"), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    credit_type = db.Column(db.String(64), nullable=False)
    credits = db.Column(db.Numeric(10, 2), nullable=False)
    source_hours = db.Column(db.Numeric(10, 2), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    student = relationship("Student", lazy="joined")
