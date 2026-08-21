from sqlalchemy.orm import relationship

from app.extensions import db


class TaskRegistration(db.Model):
    __tablename__ = "task_registrations"
    __table_args__ = (db.Index("uq_task_registration_student", "task_id", "student_id", unique=True),)

    id = db.Column(db.BigInteger, primary_key=True)
    task_id = db.Column(db.BigInteger, db.ForeignKey("college_tasks.id"), nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    apply_reason = db.Column(db.Text)
    contact_phone = db.Column(db.String(20))
    status = db.Column(db.String(32), nullable=False, default="submitted")
    selected_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    selected_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    student = relationship("Student", lazy="joined")
