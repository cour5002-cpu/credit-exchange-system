from sqlalchemy.orm import relationship

from app.extensions import db


class TaskResultSubmission(db.Model):
    __tablename__ = "task_result_submissions"
    __table_args__ = (db.Index("uq_task_result_submission_task", "task_id", unique=True),)

    id = db.Column(db.BigInteger, primary_key=True)
    task_id = db.Column(db.BigInteger, db.ForeignKey("college_tasks.id"), nullable=False)
    leader_student_id = db.Column(db.BigInteger, db.ForeignKey("students.id"), nullable=False)
    summary = db.Column(db.Text, nullable=False)
    requested_hours = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(32), nullable=False, default="submitted")
    hour_application_id = db.Column(db.BigInteger, db.ForeignKey("hour_applications.id"))
    advisor_comment = db.Column(db.Text)
    advisor_reviewed_by = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    advisor_reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    task = relationship("CollegeTask", backref="result_submissions", lazy="joined")
    leader = relationship("Student", lazy="joined")
    hour_application = relationship("HourApplication", foreign_keys=[hour_application_id], lazy="joined")
    versions = relationship(
        "TaskResultSubmissionVersion",
        cascade="all, delete-orphan",
        lazy="select",
        order_by="TaskResultSubmissionVersion.version_no",
        backref="submission",
    )
