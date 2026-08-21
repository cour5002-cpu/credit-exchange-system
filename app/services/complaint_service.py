from sqlalchemy import or_

from app.core.errors import BusinessError
from app.core.identity import current_student
from app.extensions import db
from app.models.complaint import Complaint
from app.models.student import Student
from app.models.user import User
from app.services.notification_service import create_notification
from app.services.service_helpers import add_operation, bind_attachments
from app.utils.number_generator import generate_application_no
from app.utils.pagination import paginate_query
from app.utils.time_utils import business_now


COMPLAINT_CATEGORIES = {
    "personnel_behavior",
    "service_quality",
    "process_violation",
    "other",
}
COMPLAINT_STATUSES = {"submitted", "processing", "resolved"}
HANDLING_RESULTS = {
    "substantiated",
    "partially_substantiated",
    "unsubstantiated",
    "transferred",
    "other",
}


def create_complaint(user, payload):
    current_student(user)
    payload = _object(payload, {"category", "content", "attachment_ids"}, {"category", "content"})
    category = _choice(payload["category"], COMPLAINT_CATEGORIES, "投诉分类不合法")
    content = _text(payload["content"], "content", 10, 5000)
    attachment_ids = _strict_ids(payload.get("attachment_ids"), "attachment_ids", required=False, maximum=10)
    complaint = Complaint(
        complaint_no=generate_application_no("CP"),
        submitter_user_id=user.id,
        category=category,
        content=content,
        status="submitted",
    )
    db.session.add(complaint)
    db.session.flush()
    bind_attachments("complaint", complaint.id, attachment_ids, user.id)
    add_operation(user.id, "complaint", complaint.id, "submit", None, complaint.status)
    db.session.commit()
    return complaint


def list_student_complaints(user, status, page, page_size):
    current_student(user)
    status = _list_status(status, allow_pending=False)
    query = Complaint.query.filter_by(submitter_user_id=user.id)
    if status != "all":
        query = query.filter_by(status=status)
    return paginate_query(query.order_by(Complaint.created_at.desc(), Complaint.id.desc()), page, page_size)


def get_student_complaint(user, complaint_id):
    current_student(user)
    complaint = Complaint.query.filter_by(id=complaint_id, submitter_user_id=user.id).first()
    if not complaint:
        raise BusinessError("投诉不存在", code=40401, status=404)
    return complaint


def list_complaints(status, category, keyword, page, page_size):
    status = _list_status(status, allow_pending=True)
    if category and category not in COMPLAINT_CATEGORIES:
        raise BusinessError("投诉分类不合法")
    if keyword and len(keyword) > 100:
        raise BusinessError("keyword 长度不能超过 100 个字符")
    query = Complaint.query
    if status == "pending":
        query = query.filter(Complaint.status.in_(["submitted", "processing"]))
    elif status != "all":
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if keyword:
        like = f"%{keyword}%"
        query = query.outerjoin(User, User.id == Complaint.submitter_user_id).outerjoin(
            Student, Student.user_id == User.id
        ).filter(or_(
            Complaint.complaint_no.like(like),
            Complaint.content.like(like),
            User.real_name.like(like),
            Student.name.like(like),
            Student.student_no.like(like),
        ))
    return paginate_query(query.order_by(Complaint.created_at.desc(), Complaint.id.desc()), page, page_size)


def get_complaint(complaint_id, mark_viewed=False):
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        raise BusinessError("投诉不存在", code=40401, status=404)
    if mark_viewed and complaint.viewed_at is None:
        complaint.viewed_at = business_now()
        db.session.commit()
    return complaint


def start_complaint_processing(user, complaint_id):
    complaint = Complaint.query.filter_by(id=complaint_id).with_for_update().first()
    if not complaint:
        raise BusinessError("投诉不存在", code=40401, status=404)
    if complaint.status != "submitted":
        raise BusinessError("当前投诉状态不允许开始处理", code=40901, status=409)
    now = business_now()
    complaint.status = "processing"
    complaint.viewed_at = complaint.viewed_at or now
    complaint.processing_started_at = now
    add_operation(user.id, "complaint", complaint.id, "start_processing", "submitted", "processing")
    db.session.commit()
    return complaint


def resolve_complaint(user, complaint_id, payload):
    payload = _object(payload, {"handling_result", "handling_opinion"}, {"handling_result", "handling_opinion"})
    result = _choice(payload["handling_result"], HANDLING_RESULTS, "处理结果不合法")
    opinion = _text(payload["handling_opinion"], "handling_opinion", 1, 4000)
    complaint = Complaint.query.filter_by(id=complaint_id).with_for_update().first()
    if not complaint:
        raise BusinessError("投诉不存在", code=40401, status=404)
    if complaint.status not in {"submitted", "processing"}:
        raise BusinessError("当前投诉状态不允许完成处理", code=40901, status=409)
    before = complaint.status
    now = business_now()
    complaint.status = "resolved"
    complaint.viewed_at = complaint.viewed_at or now
    complaint.processing_started_at = complaint.processing_started_at or now
    complaint.handled_by = user.id
    complaint.handling_result = result
    complaint.handling_opinion = opinion
    complaint.handled_at = now
    add_operation(user.id, "complaint", complaint.id, "resolved", before, "resolved")
    notification = create_notification(
        complaint.submitter_user_id,
        user.id,
        "complaint",
        "complaint_resolved",
        "投诉处理已完成",
        f"您的投诉“{complaint.complaint_no}”已处理完成，请查看处理结果。",
        biz_type="complaint",
        biz_id=complaint.id,
        payload={
            "complaint_no": complaint.complaint_no,
            "status": complaint.status,
            "handling_result": complaint.handling_result,
        },
        dedupe_key=f"complaint:{complaint.id}:resolved",
    )
    if notification is None:
        raise BusinessError("投诉学生账号不可用，不能完成处理", code=40902, status=409)
    db.session.commit()
    return complaint


def _list_status(value, allow_pending):
    value = (value or "all").strip()
    allowed = COMPLAINT_STATUSES | {"all"}
    if allow_pending:
        allowed.add("pending")
    if value not in allowed:
        raise BusinessError("status 不合法")
    return value


def _choice(value, choices, message):
    if not isinstance(value, str) or value.strip() not in choices:
        raise BusinessError(message)
    return value.strip()


def _text(value, field, minimum, maximum):
    if not isinstance(value, str):
        raise BusinessError(f"{field} 必须是字符串")
    value = value.strip()
    if not minimum <= len(value) <= maximum:
        raise BusinessError(f"{field} 长度必须在 {minimum} 到 {maximum} 个字符之间")
    return value


def _strict_ids(value, field, required, maximum):
    if value is None and not required:
        return []
    if not isinstance(value, list) or (required and not value) or len(value) > maximum:
        raise BusinessError(f"{field} 必须是最多 {maximum} 项的数组")
    if any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in value):
        raise BusinessError(f"{field} 只能包含正整数")
    if len(set(value)) != len(value):
        raise BusinessError(f"{field} 不能包含重复 ID")
    return value


def _object(value, allowed, required):
    if not isinstance(value, dict):
        raise BusinessError("请求体必须是 JSON 对象")
    fields = set(value)
    if fields - allowed:
        raise BusinessError("请求包含未定义字段")
    if required - fields:
        raise BusinessError("请求缺少必填字段")
    return value
