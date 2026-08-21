from sqlalchemy.orm import relationship

from app.extensions import db


class Notification(db.Model):
    __tablename__ = "notifications"
    __table_args__ = (
        db.UniqueConstraint("recipient_user_id", "dedupe_key", name="uq_notifications_recipient_dedupe"),
        db.Index("ix_notifications_recipient_period_created", "recipient_user_id", "academic_year", "semester", "created_at", "id"),
        db.Index("ix_notifications_recipient_period_read", "recipient_user_id", "academic_year", "semester", "read_at", "id"),
        db.Index("ix_notifications_batch_recipient", "announcement_batch_key", "recipient_user_id"),
        db.Index("ix_notifications_replaced_batch", "replaced_by_batch_key"),
        db.Index("ix_notifications_business", "biz_type", "biz_id"),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    recipient_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    actor_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    category = db.Column(db.String(32), nullable=False)
    message_type = db.Column(db.String(64), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    biz_type = db.Column(db.String(64))
    biz_id = db.Column(db.BigInteger)
    payload = db.Column(db.JSON)
    academic_year = db.Column(db.String(16), nullable=False)
    semester = db.Column(db.String(16), nullable=False)
    announcement_batch_key = db.Column(db.String(64))
    announcement_audience = db.Column(db.String(255))
    replaced_by_batch_key = db.Column(db.String(64))
    expires_at = db.Column(db.DateTime)
    stopped_at = db.Column(db.DateTime)
    withdrawn_at = db.Column(db.DateTime)
    dedupe_key = db.Column(db.String(200), nullable=False)
    read_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    recipient = relationship("User", foreign_keys=[recipient_user_id], lazy="joined")
    actor = relationship("User", foreign_keys=[actor_user_id], lazy="joined")
