from app.extensions import db


class StudentHourTransaction(db.Model):
    __tablename__ = "student_hour_transactions"

    id = db.Column(db.BigInteger, primary_key=True)
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    biz_type = db.Column(db.String(32), nullable=False)
    biz_id = db.Column(db.BigInteger, nullable=False)
    change_type = db.Column(db.String(20), nullable=False)
    hours_change = db.Column(db.Numeric(10, 2), nullable=False)
    before_hours = db.Column(db.Numeric(10, 2), nullable=False)
    after_hours = db.Column(db.Numeric(10, 2), nullable=False)
    remark = db.Column(db.String(255))
    created_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
