from datetime import datetime
from decimal import Decimal

from app.extensions import db
from app.models.hour_application import HourApplication
from app.models.hour_application_review import HourApplicationReview
from app.services.hour_account_service import add_hours
from app.utils.time_utils import business_now


def get_teacher_application_detail(application_id, teacher_id):
    return HourApplication.query.filter_by(
        id=application_id,
        assigned_teacher_id=teacher_id,
    ).first()


def submit_review(application, teacher_id, user_id, form):
    action = form.action.data
    approved_hours = form.approved_hours.data

    review = HourApplicationReview(
        application_id=application.id,
        reviewer_teacher_id=teacher_id,
        action=action,
        comment=form.comment.data,
        approved_hours=approved_hours if approved_hours is not None else None,
    )
    db.session.add(review)

    if action == "approve":
        final_hours = (
            Decimal(str(approved_hours))
            if approved_hours is not None
            else Decimal(str(application.requested_hours))
        )
        application.status = "approved"
        application.final_hours = final_hours
        application.reviewed_at = business_now()
        add_hours(
            student_id=application.student_id,
            hours=final_hours,
            biz_type="hour_application",
            biz_id=application.id,
            created_by=user_id,
            remark=f"课时申请 {application.application_no} 审核通过",
        )
    else:
        application.status = "rejected"
        application.final_hours = Decimal("0.00")
        application.reviewed_at = business_now()

    db.session.commit()
    return review
