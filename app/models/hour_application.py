from sqlalchemy.orm import relationship

from app.extensions import db


class HourApplication(db.Model):
    __tablename__ = "hour_applications"

    TASK_TYPE_LABELS = {
        "project": "项目类",
        "practice": "实践类",
        "competition": "竞赛类",
        "certificate": "证书类",
    }
    STATUS_LABELS = {
        "submitted": "待分配",
        "assigned": "待审核",
        "approved": "已通过",
        "rejected": "已驳回",
    }

    id = db.Column(db.BigInteger, primary_key=True)
    application_no = db.Column(db.String(64), unique=True, nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    title = db.Column(db.Text, nullable=False)
    participant_members = db.Column(db.Text)
    major_name = db.Column(db.String(128))
    course_name = db.Column(db.String(128))
    instructor_name = db.Column(db.String(128))
    achievement_submission = db.Column(db.Text)
    task_type_code = db.Column(db.String(64), nullable=False)
    requested_hours = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), nullable=False, default="submitted")
    assigned_teacher_id = db.Column(db.BigInteger, db.ForeignKey("teachers.id"))
    final_hours = db.Column(db.Numeric(10, 2))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    student = relationship("Student", lazy="joined")
    assigned_teacher = relationship("Teacher", lazy="joined")

    @property
    def task_type_name(self):
        return self.TASK_TYPE_LABELS.get(self.task_type_code, self.task_type_code)

    @property
    def status_name(self):
        return self.STATUS_LABELS.get(self.status, self.status)
