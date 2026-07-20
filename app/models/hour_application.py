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
        "draft": "草稿",
        "submitted": "待指导老师确认",
        "advisor_approved": "指导老师已确认",
        "advisor_rejected": "指导老师已驳回",
        "pending_material": "待补交成果",
        "extension_requested": "已申请延期",
        "extension_admin_review": "特殊延期待管理员审核",
        "extension_rejected": "延期已驳回",
        "material_overdue": "成果逾期未提交",
        "material_submitted": "成果已补交",
        "pending_assignment": "待分配审核老师",
        "pending_review": "待审核老师审核",
        "reviewer_approved": "审核老师已通过",
        "reviewer_modified_approved": "审核老师已修改并通过",
        "reviewer_rejected": "审核老师已驳回",
        "pending_admin_final": "待管理员最终确认",
        "final_approved": "最终通过",
        "final_rejected": "最终驳回",
        "closed": "已关闭",
        "discarded": "已删除",
        # Legacy statuses kept for old server-rendered pages.
        "assigned": "待审核",
        "approved": "已通过",
        "rejected": "已驳回",
    }

    id = db.Column(db.BigInteger, primary_key=True)
    application_no = db.Column(db.String(64), unique=True, nullable=False)
    student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    applicant_student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"))
    leader_student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"))
    application_type = db.Column(db.String(32), nullable=False, default="with_material")
    source_type = db.Column(db.String(32), nullable=False, default="student_self")
    source_task_id = db.Column(db.BigInteger)
    task_result_submission_id = db.Column(db.BigInteger)
    task_type_id = db.Column(db.BigInteger, db.ForeignKey("task_types.id"))
    title = db.Column(db.Text, nullable=False)
    participant_members = db.Column(db.Text)
    major_name = db.Column(db.String(128))
    course_name = db.Column(db.String(128))
    instructor_name = db.Column(db.String(128))
    achievement_submission = db.Column(db.Text)
    task_type_code = db.Column(db.String(64), nullable=False)
    requested_hours = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(32), nullable=False, default="submitted")
    assigned_teacher_id = db.Column(db.BigInteger, db.ForeignKey("teachers.id"))
    reviewer_suggested_hours = db.Column(db.Numeric(10, 2))
    final_hours = db.Column(db.Numeric(10, 2))
    achievement_summary = db.Column(db.Text)
    material_due_at = db.Column(db.DateTime)
    extension_count = db.Column(db.Integer, nullable=False, default=0)
    appeal_advice = db.Column(db.Text)
    appeal_id = db.Column(db.BigInteger)
    submitted_at = db.Column(db.DateTime)
    advisor_reviewed_at = db.Column(db.DateTime)
    reviewer_reviewed_at = db.Column(db.DateTime)
    final_reviewed_at = db.Column(db.DateTime)
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    student = relationship("Student", foreign_keys=[student_id], lazy="joined")
    applicant = relationship("Student", foreign_keys=[applicant_student_id], lazy="joined")
    leader = relationship("Student", foreign_keys=[leader_student_id], lazy="joined")
    task_type = relationship("TaskType", lazy="joined")
    assigned_teacher = relationship("Teacher", lazy="joined")
    attachments = relationship("HourApplicationAttachment", lazy="select")
    reviews = relationship("HourApplicationReview", lazy="select")

    @property
    def task_type_name(self):
        if self.task_type:
            return self.task_type.type_name
        return self.TASK_TYPE_LABELS.get(self.task_type_code, self.task_type_code)

    @property
    def status_name(self):
        return self.STATUS_LABELS.get(self.status, self.status)
