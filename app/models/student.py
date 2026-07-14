from app.extensions import db


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    student_no = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    gender = db.Column(db.String(16))
    college = db.Column(db.String(128))
    major = db.Column(db.String(128))
    grade = db.Column(db.String(32))
    class_name = db.Column(db.String(64))
    status = db.Column(db.String(20), nullable=False, default="active")
    import_batch_no = db.Column(db.String(64))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )
