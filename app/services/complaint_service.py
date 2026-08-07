from app.core.errors import BusinessError
from app.core.identity import current_student
from app.extensions import db
from app.models.complaint import Complaint
from app.services.service_helpers import (
    add_operation,
    bind_attachments,
    required_str,
)
from app.utils.pagination import finish_query
from app.utils.time_utils import business_now


def create_complaint(user, payload):
    current_student(user)
    complaint = Complaint(
        submitter_user_id=user.id,
        content=required_str(payload, "content"),
        status="submitted",
    )
    db.session.add(complaint)
    db.session.flush()
    bind_attachments("complaint", complaint.id, payload.get("attachment_ids"), user.id)
    add_operation(user.id, "complaint", complaint.id, "submit", None, complaint.status)
    db.session.commit()
    return complaint


def list_complaints(status=None, page=None, page_size=None):
    query = Complaint.query
    if status:
        query = query.filter_by(status=status)
    return finish_query(query.order_by(Complaint.id.desc()), page, page_size)


def get_complaint(complaint_id, mark_viewed=False):
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        raise BusinessError("投诉不存在", code=40401, status=404)
    if mark_viewed and complaint.status == "submitted":
        complaint.status = "viewed"
        complaint.viewed_at = business_now()
        db.session.commit()
    return complaint
