from app.extensions import db


class CreditExchangeRecord(db.Model):
    __tablename__ = "credit_exchange_records"

    id = db.Column(db.BigInteger, primary_key=True)
    exchange_application_id = db.Column(
        db.BigInteger,
        db.ForeignKey("credit_exchange_applications.id"),
        nullable=False,
        unique=True,
    )
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    used_hours = db.Column(db.Numeric(10, 2), nullable=False)
    exchanged_credits = db.Column(db.Numeric(10, 2), nullable=False)
    total_used_hours = db.Column(db.Numeric(10, 2))
    total_credits = db.Column(db.Numeric(10, 2))
    rule_snapshot = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
