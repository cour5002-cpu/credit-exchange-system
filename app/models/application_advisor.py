from sqlalchemy.orm import relationship

from app.extensions import db


class ApplicationAdvisor(db.Model):
    __tablename__ = "application_advisors"

    id = db.Column(db.BigInteger, primary_key=True)
    application_id = db.Column(db.BigInteger, db.ForeignKey("hour_applications.id"), nullable=False)
    teacher_id = db.Column(db.BigInteger, db.ForeignKey("teachers.id"), nullable=False)
    advisor_role = db.Column(db.String(20), nullable=False, default="primary")
    can_operate = db.Column(db.Boolean, nullable=False, default=False)
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    application = relationship("HourApplication", backref="advisor_links")
    teacher = relationship("Teacher", lazy="joined")
