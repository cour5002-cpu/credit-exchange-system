from sqlalchemy.orm import relationship

from app.extensions import db


class CollegeTask(db.Model):
    __tablename__ = "college_tasks"

    id = db.Column(db.BigInteger, primary_key=True)
    task_no = db.Column(db.String(64), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    task_type_id = db.Column(db.BigInteger, db.ForeignKey("task_types.id"), nullable=False)
    major_name = db.Column(db.String(128), nullable=False)
    course_name = db.Column(db.String(128), nullable=False)
    requirement = db.Column(db.Text, nullable=False)
    publisher_type = db.Column(db.String(20), nullable=False)
    publisher_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    advisor_teacher_id = db.Column(db.BigInteger, db.ForeignKey("teachers.id"), nullable=False)
    registration_start_at = db.Column(db.DateTime)
    registration_deadline = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(32), nullable=False, default="draft")
    admin_reviewed_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    admin_review_comment = db.Column(db.Text)
    published_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    task_type = relationship("TaskType", lazy="joined")
    advisor = relationship("Teacher", lazy="joined")
    publisher = relationship("User", foreign_keys=[publisher_user_id], lazy="joined")
    registrations = relationship("TaskRegistration", cascade="all, delete-orphan", lazy="select", backref="task")
    members = relationship("TaskMember", cascade="all, delete-orphan", lazy="select", backref="task")
