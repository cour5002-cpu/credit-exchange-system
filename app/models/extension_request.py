from sqlalchemy.orm import relationship

from app.extensions import db


class ExtensionRequest(db.Model):
    __tablename__ = "extension_requests"

    id = db.Column(db.BigInteger, primary_key=True)
    application_id = db.Column(
        db.BigInteger,
        db.ForeignKey("hour_applications.id"),
        nullable=False,
        unique=True,
    )
    old_due_at = db.Column(db.DateTime, nullable=False)
    requested_due_at = db.Column(db.DateTime, nullable=False)
    extension_days = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    review_level = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="pending_advisor_review")
    reviewed_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    review_comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    reviewed_at = db.Column(db.DateTime)

    application = relationship("HourApplication", backref="extension_requests")
    reviewer = relationship("User", lazy="joined")
