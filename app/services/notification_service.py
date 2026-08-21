import re

from sqlalchemy import func

from app.core.errors import BusinessError
from app.extensions import db
from app.models.notification import Notification
from app.models.system_config import SystemConfig
from app.models.user import User
from app.utils.pagination import paginate_query
from app.utils.time_utils import business_now


ACADEMIC_YEAR_RE = re.compile(r"^(\d{4})-(\d{4})$")
VALID_CATEGORIES = {"task", "hour_application", "extension", "complaint", "appeal", "credit_exchange", "rule", "announcement"}


def validate_period(academic_year, semester):
    match = ACADEMIC_YEAR_RE.fullmatch(str(academic_year or ""))
    if not match or int(match.group(2)) != int(match.group(1)) + 1:
        raise BusinessError("academic_year 格式不正确")
    semester = str(semester or "")
    if semester not in {"1", "2"}:
        raise BusinessError("semester 只能是 1 或 2")
    return str(academic_year), semester


def current_period():
    values = {
        item.config_key: item.config_value
        for item in SystemConfig.query.filter(SystemConfig.config_key.in_(["current_academic_year", "current_semester"])).all()
    }
    try:
        return validate_period(values.get("current_academic_year"), values.get("current_semester"))
    except BusinessError as exc:
        raise BusinessError("当前学年学期配置不可用", code=50301, status=503) from exc


def resolve_period(academic_year=None, semester=None):
    if (academic_year is None) != (semester is None):
        raise BusinessError("academic_year 和 semester 必须同时提供")
    return current_period() if academic_year is None else validate_period(academic_year, semester)


def create_notification(recipient_user_id, actor_user_id, category, message_type, title, content,
                        biz_type=None, biz_id=None, payload=None, dedupe_key=None,
                        academic_year=None, semester=None, **extra):
    if category not in VALID_CATEGORIES:
        raise BusinessError("消息类别不合法")
    recipient = db.session.get(User, recipient_user_id)
    if not recipient or recipient.status != "active":
        return None
    academic_year, semester = resolve_period(academic_year, semester)
    dedupe_key = str(dedupe_key or "").strip()
    if not dedupe_key or len(dedupe_key) > 200:
        raise BusinessError("消息幂等键不合法")
    existing = Notification.query.filter_by(recipient_user_id=recipient_user_id, dedupe_key=dedupe_key).first()
    if existing:
        return existing
    item = Notification(
        recipient_user_id=recipient_user_id,
        actor_user_id=actor_user_id,
        category=category,
        message_type=message_type,
        title=str(title)[:200],
        content=str(content),
        biz_type=biz_type,
        biz_id=biz_id,
        payload=payload,
        academic_year=academic_year,
        semester=semester,
        dedupe_key=dedupe_key,
        **extra,
    )
    db.session.add(item)
    db.session.flush()
    return item


def list_notifications(user_id, status, academic_year, semester, page, page_size):
    if status not in {"all", "read", "unread"}:
        raise BusinessError("status 只能是 all、read 或 unread")
    used_default_period = academic_year is None
    academic_year, semester = resolve_period(academic_year, semester)
    query = Notification.query.filter_by(
        recipient_user_id=user_id, academic_year=academic_year, semester=semester
    )
    if status == "read":
        query = query.filter(Notification.read_at.isnot(None))
    elif status == "unread":
        query = query.filter(Notification.read_at.is_(None))
    result = paginate_query(query.order_by(Notification.created_at.desc(), Notification.id.desc()), page, page_size)
    periods = db.session.query(Notification.academic_year, Notification.semester).filter_by(recipient_user_id=user_id).distinct().all()
    period_set = {(row[0], row[1]) for row in periods}
    try:
        period_set.add(current_period())
    except BusinessError:
        if used_default_period:
            raise
    available = [{"academic_year": y, "semester": s} for y, s in sorted(period_set, key=lambda x: (x[0], x[1]), reverse=True)]
    return result, (academic_year, semester), available


def unread_summary(user_id, academic_year=None, semester=None):
    academic_year, semester = resolve_period(academic_year, semester)
    base = Notification.query.filter_by(recipient_user_id=user_id, academic_year=academic_year, semester=semester)
    return {
        "unread_count": base.filter(Notification.read_at.is_(None)).count(),
        "latest_notification_id": base.with_entities(func.max(Notification.id)).scalar(),
        "academic_year": academic_year,
        "semester": semester,
    }


def get_owned_notification(user_id, notification_id):
    item = Notification.query.filter_by(id=notification_id, recipient_user_id=user_id).first()
    if not item:
        raise BusinessError("消息不存在", code=40401, status=404)
    return item


def mark_read(user_id, notification_id):
    item = get_owned_notification(user_id, notification_id)
    if item.read_at is None:
        item.read_at = business_now()
        db.session.commit()
    return item


def mark_selected_read(user_id, ids):
    if not isinstance(ids, list) or not 1 <= len(ids) <= 100:
        raise BusinessError("ids 必须是包含 1 到 100 项的数组")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in ids) or len(set(ids)) != len(ids):
        raise BusinessError("ids 必须是互不重复的正整数")
    items = Notification.query.filter(Notification.id.in_(ids), Notification.recipient_user_id == user_id).all()
    if len(items) != len(ids):
        raise BusinessError("消息不存在", code=40401, status=404)
    now = business_now()
    newly = 0
    for item in items:
        if item.read_at is None:
            item.read_at = now
            newly += 1
    db.session.commit()
    return {"requested_count": len(ids), "newly_read_count": newly, "already_read_count": len(ids) - newly}


def mark_all_read(user_id, up_to_id, academic_year, semester):
    if isinstance(up_to_id, bool) or not isinstance(up_to_id, int) or up_to_id <= 0:
        raise BusinessError("up_to_id 必须是正整数")
    academic_year, semester = validate_period(academic_year, semester)
    count = Notification.query.filter(
        Notification.recipient_user_id == user_id,
        Notification.academic_year == academic_year,
        Notification.semester == semester,
        Notification.id <= up_to_id,
        Notification.read_at.is_(None),
    ).update({Notification.read_at: business_now()}, synchronize_session=False)
    db.session.commit()
    return {"updated_count": count, "up_to_id": up_to_id, "academic_year": academic_year, "semester": semester}


def business_available(item, user):
    if not item.biz_type or not item.biz_id:
        return False
    from app.models.appeal import Appeal
    from app.models.application_advisor import ApplicationAdvisor
    from app.models.college_task import CollegeTask
    from app.models.complaint import Complaint
    from app.models.credit_exchange_application import CreditExchangeApplication
    from app.models.extension_request import ExtensionRequest
    from app.models.hour_application import HourApplication
    from app.models.hour_application_member import HourApplicationMember
    from app.models.review_assignment import ReviewAssignment
    from app.models.rule_file import RuleFile
    from app.models.student import Student
    from app.models.teacher import Teacher

    if item.biz_type == "rule_file":
        return RuleFile.query.filter_by(id=item.biz_id, status="active").first() is not None
    if item.biz_type == "complaint":
        complaint = db.session.get(Complaint, item.biz_id)
        return bool(complaint and (user.has_role("admin") or complaint.submitter_user_id == user.id))
    student = Student.query.filter_by(user_id=user.id, status="active").first()
    teacher = Teacher.query.filter_by(user_id=user.id, status="active").first()
    if item.biz_type == "college_task":
        task = db.session.get(CollegeTask, item.biz_id)
        return bool(task and (user.has_role("admin") or task.publisher_user_id == user.id
                              or (teacher and task.advisor_teacher_id == teacher.id)
                              or (student and task.status not in {"draft", "pending_publish_review", "publish_rejected"})))
    if item.biz_type == "hour_application":
        application = db.session.get(HourApplication, item.biz_id)
        if not application:
            return False
        return bool(user.has_role("admin")
                    or (student and (application.student_id == student.id
                                     or application.applicant_student_id == student.id
                                     or HourApplicationMember.query.filter_by(application_id=application.id, student_id=student.id, status="active").first()))
                    or (teacher and (ApplicationAdvisor.query.filter_by(application_id=application.id, teacher_id=teacher.id).first()
                                     or ReviewAssignment.query.filter_by(application_id=application.id, reviewer_teacher_id=teacher.id).first())))
    if item.biz_type == "extension_request":
        extension = db.session.get(ExtensionRequest, item.biz_id)
        if not extension:
            return False
        proxy = type("BusinessRef", (), {"biz_type": "hour_application", "biz_id": extension.application_id})()
        return business_available(proxy, user)
    if item.biz_type == "appeal":
        appeal = db.session.get(Appeal, item.biz_id)
        if not appeal:
            return False
        if user.has_role("admin") or (student and appeal.applicant_student_id == student.id):
            return True
        if not teacher:
            return False
        if appeal.target_type == "hour_application":
            return ApplicationAdvisor.query.filter_by(
                application_id=appeal.target_id,
                teacher_id=teacher.id,
                advisor_role="primary",
                can_operate=True,
            ).first() is not None
        if appeal.target_type == "credit_exchange":
            exchange = db.session.get(CreditExchangeApplication, appeal.target_id)
            return bool(exchange and exchange.advisor_teacher_id == teacher.id)
        return False
    if item.biz_type == "credit_exchange":
        exchange = db.session.get(CreditExchangeApplication, item.biz_id)
        return bool(exchange and (user.has_role("admin")
                                  or (student and (exchange.student_id == student.id or exchange.applicant_student_id == student.id
                                                   or any(x.student_id == student.id for x in exchange.allocations)))
                                  or (teacher and exchange.advisor_teacher_id == teacher.id)))
    return False
