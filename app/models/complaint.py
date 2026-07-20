from app.extensions import db


class Complaint(db.Model):
    __tablename__ = "complaints"

    id = db.Column(db.BigInteger, primary_key=True)
    submitter_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="submitted")
    viewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

