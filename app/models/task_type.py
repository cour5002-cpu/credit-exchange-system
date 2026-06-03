from app.extensions import db


class TaskType(db.Model):
    __tablename__ = "task_types"

    id = db.Column(db.BigInteger, primary_key=True)
    type_code = db.Column(db.String(64), unique=True, nullable=False)
    type_name = db.Column(db.String(64), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="enabled")
    sort_order = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )
