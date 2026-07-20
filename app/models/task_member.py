from sqlalchemy.orm import relationship

from app.extensions import db


class TaskMember(db.Model):
    __tablename__ = "task_members"
    __table_args__ = (db.Index("uq_task_member_student", "task_id", "student_id", unique=True),)

    id = db.Column(db.BigInteger, primary_key=True)
    task_id = db.Column(db.BigInteger, db.ForeignKey("college_tasks.id"), nullable=False)
    registration_id = db.Column(db.BigInteger, db.ForeignKey("task_registrations.id"))
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    is_leader = db.Column(db.Boolean, nullable=False, default=False)
    selected_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    registration = relationship("TaskRegistration", lazy="joined")
    student = relationship("Student", lazy="joined")
