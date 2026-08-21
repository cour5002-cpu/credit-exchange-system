from sqlalchemy.orm import relationship

from app.extensions import db


class HourApplicationMember(db.Model):
    __tablename__ = "hour_application_members"

    id = db.Column(db.BigInteger, primary_key=True)
    application_id = db.Column(db.BigInteger, db.ForeignKey("hour_applications.id"), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    is_leader = db.Column(db.Boolean, nullable=False, default=False)
    can_view = db.Column(db.Boolean, nullable=False, default=True)
    can_apply_credit_exchange = db.Column(db.Boolean, nullable=False, default=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    joined_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    application = relationship("HourApplication", backref="member_links")
    student = relationship("Student", lazy="joined")
