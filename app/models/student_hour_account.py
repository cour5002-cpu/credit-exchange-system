from app.extensions import db


class StudentHourAccount(db.Model):
    __tablename__ = "student_hour_accounts"

    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(
        db.BigInteger,
        db.ForeignKey("students.id"),
        nullable=False,
        unique=True,
    )
    total_earned_hours = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    total_exchanged_hours = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    available_hours = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )
