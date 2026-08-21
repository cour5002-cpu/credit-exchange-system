from sqlalchemy.orm import relationship

from app.extensions import db


class Complaint(db.Model):
    __tablename__ = "complaints"
    __table_args__ = (
        db.Index("ix_complaints_status_created", "status", "created_at", "id"),
        db.Index("ix_complaints_submitter_created", "submitter_user_id", "created_at", "id"),
        db.Index("ix_complaints_category_status_created", "category", "status", "created_at", "id"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    complaint_no = db.Column(db.String(64), unique=True, nullable=False)
    submitter_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    category = db.Column(db.String(32), nullable=False, default="other")
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="submitted")
    viewed_at = db.Column(db.DateTime)
    processing_started_at = db.Column(db.DateTime)
    handled_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    handling_result = db.Column(db.String(32))
    handling_opinion = db.Column(db.Text)
    handled_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    submitter = relationship("User", foreign_keys=[submitter_user_id], lazy="joined")
    handler = relationship("User", foreign_keys=[handled_by], lazy="joined")
