from sqlalchemy.orm import relationship

from app.extensions import db


class TaskResultSubmissionVersion(db.Model):
    __tablename__ = "task_result_submission_versions"
    __table_args__ = (
        db.UniqueConstraint(
            "submission_id",
            "version_no",
            name="uq_task_result_submission_version",
        ),
    )

    id = db.Column(db.BigInteger, primary_key=True)
    submission_id = db.Column(
        db.BigInteger,
        db.ForeignKey("task_result_submissions.id"),
        nullable=False,
    )
    version_no = db.Column(db.Integer, nullable=False)
    summary = db.Column(db.Text, nullable=False)
    requested_hours = db.Column(db.Numeric(10, 2), nullable=False)
    attachment_ids = db.Column(db.JSON, nullable=False, default=list)
    submitted_by = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    submitter = relationship("User", lazy="joined")
