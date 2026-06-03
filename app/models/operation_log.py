from app.extensions import db


class OperationLog(db.Model):
    __tablename__ = "operation_logs"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    module = db.Column(db.String(64), nullable=False)
    biz_type = db.Column(db.String(64), nullable=False)
    biz_id = db.Column(db.BigInteger)
    action = db.Column(db.String(64), nullable=False)
    detail = db.Column(db.Text)
    ip = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
