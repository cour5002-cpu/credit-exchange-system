from app.extensions import db


class HourApplicationAttachment(db.Model):
    __tablename__ = "hour_application_attachments"

    id = db.Column(db.BigInteger, primary_key=True)
    application_id = db.Column(
        db.BigInteger,
        db.ForeignKey("hour_applications.id"),
        nullable=False,
    )
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.BigInteger)
    file_type = db.Column(db.String(64))
    uploaded_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    @property
    def static_relative_path(self):
        prefix = "static/"
        if self.file_path.startswith(prefix):
            return self.file_path[len(prefix):]
        return self.file_path
