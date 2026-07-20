from sqlalchemy.orm import relationship

from app.extensions import db


class CreditConversionRule(db.Model):
    __tablename__ = "credit_conversion_rules"

    id = db.Column(db.BigInteger, primary_key=True)
    rule_name = db.Column(db.String(128), nullable=False)
    hours_per_credit = db.Column(db.Numeric(10, 2), nullable=False)
    max_single_exchange_hours = db.Column(db.Numeric(10, 2), nullable=False)
    rounding_mode = db.Column(db.String(32), nullable=False)
    effective_at = db.Column(db.DateTime, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    rule_file_id = db.Column(db.BigInteger, db.ForeignKey("rule_files.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    rule_file = relationship("RuleFile", lazy="joined")
