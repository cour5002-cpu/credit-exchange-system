from sqlalchemy.orm import relationship

from app.extensions import db


class ReviewAssignment(db.Model):
    __tablename__ = "review_assignments"

    id = db.Column(db.BigInteger, primary_key=True)
    application_id = db.Column(db.BigInteger, db.ForeignKey("hour_applications.id"), nullable=False)
    reviewer_teacher_id = db.Column(db.BigInteger, db.ForeignKey("teachers.id"), nullable=False)
    assigned_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    assign_reason = db.Column(db.String(255))
    status = db.Column(db.String(20), nullable=False, default="active")
    assigned_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    application = relationship("HourApplication", backref="review_assignments")
    reviewer = relationship("Teacher", lazy="joined")
