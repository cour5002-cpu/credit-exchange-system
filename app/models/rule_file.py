from sqlalchemy.orm import relationship

from app.extensions import db


class RuleFile(db.Model):
    __tablename__ = "rule_files"

    id = db.Column(db.BigInteger, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    rule_type = db.Column(db.String(64), nullable=False)
    usage_type = db.Column(db.String(32), nullable=False)
    description = db.Column(db.Text)
    attachment_id = db.Column(db.BigInteger, db.ForeignKey("attachments.id"), nullable=False)
    version_no = db.Column(db.String(64))
    status = db.Column(db.String(20), nullable=False, default="active")
    uploaded_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    attachment = relationship("Attachment", lazy="joined")
