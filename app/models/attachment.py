from app.extensions import db


class Attachment(db.Model):
    __tablename__ = "attachments"

    id = db.Column(db.BigInteger, primary_key=True)
    biz_type = db.Column(db.String(64), nullable=False)
    owner_type = db.Column(db.String(64))
    owner_id = db.Column(db.BigInteger)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger, nullable=False, default=0)
    mime_type = db.Column(db.String(128))
    uploaded_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    voided_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    voided_at = db.Column(db.DateTime)
    void_reason = db.Column(db.Text)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
