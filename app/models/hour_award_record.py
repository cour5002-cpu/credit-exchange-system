from sqlalchemy.orm import relationship

from app.extensions import db


class HourAwardRecord(db.Model):
    __tablename__ = "hour_award_records"

    id = db.Column(db.BigInteger, primary_key=True)
    application_id = db.Column(db.BigInteger, db.ForeignKey("hour_applications.id"), nullable=False, unique=True)
    leader_student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    total_hours = db.Column(db.Numeric(10, 2), nullable=False)
    source_type = db.Column(db.String(32), nullable=False)
    awarded_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    awarded_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    is_exchanged = db.Column(db.Boolean, nullable=False, default=False)
    remark = db.Column(db.String(255))

    application = relationship("HourApplication", lazy="joined")
    leader = relationship("Student", lazy="joined")
