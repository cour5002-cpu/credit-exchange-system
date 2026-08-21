from app.extensions import db


class HourApplicationReview(db.Model):
    __tablename__ = "hour_application_reviews"

    ACTION_LABELS = {
        "approve": "通过",
        "reject": "驳回",
        "approved": "通过",
        "rejected": "驳回",
        "modified_approved": "修改并通过",
    }

    id = db.Column(db.BigInteger, primary_key=True)
    application_id = db.Column(
        db.BigInteger,
        db.ForeignKey("hour_applications.id"),
        nullable=False,
    )
    reviewer_teacher_id = db.Column(
        db.BigInteger,
        db.ForeignKey("teachers.id"),
        nullable=True,
    )
    operator_user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"))
    operator_teacher_id = db.Column(db.BigInteger, db.ForeignKey("teachers.id"))
    stage = db.Column(db.String(32))
    operator_role = db.Column(db.String(32))
    decision = db.Column(db.String(32))
    before_status = db.Column(db.String(32))
    after_status = db.Column(db.String(32))
    requested_hours_snapshot = db.Column(db.Numeric(10, 2))
    action = db.Column(db.String(20), nullable=False)
    comment = db.Column(db.Text)
    approved_hours = db.Column(db.Numeric(10, 2))
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)

    @property
    def action_name(self):
        return self.ACTION_LABELS.get(self.action, self.action)
