from datetime import timedelta
from math import ceil

from app.core.errors import BusinessError
from app.core.identity import current_student, current_teacher
from app.extensions import db
from app.models.application_advisor import ApplicationAdvisor
from app.models.attachment import Attachment
from app.models.extension_request import ExtensionRequest
from app.models.hour_application import HourApplication
from app.models.hour_application_member import HourApplicationMember
from app.models.hour_application_review import HourApplicationReview
from app.models.operation_log import OperationLog
from app.services.extension_rule_service import current_extension_rule, extension_rule_snapshot
from app.services.notification_service import create_notification
from app.utils.pagination import finish_query
from app.utils.time_utils import business_now, parse_api_datetime


PENDING_EXTENSION_STATUSES = {"pending_advisor_review", "pending_admin_review"}


def create_extension_request(user, application_id, payload):
    if not isinstance(payload, dict):
        raise BusinessError("请求体必须是 JSON 对象")
    allowed_fields = {"requested_due_at", "reason", "attachment_ids"}
    if set(payload) - allowed_fields:
        raise BusinessError("请求包含未定义字段")
    student = current_student(user)
    application = HourApplication.query.filter_by(id=application_id).with_for_update().first()
    if not application or not _student_can_manage(student.id, application):
        raise BusinessError("课时申请不存在或不可见", code=40401, status=404)
    if application.application_type != "without_material":
        raise BusinessError("只有无成果申请可以申请延期", code=40901, status=409)
    if application.leader_student_id != student.id and application.applicant_student_id != student.id:
        raise BusinessError("只有申请发起人或队长可以申请延期", code=40301, status=403)
    _require_status(application, "pending_material")

    history = ExtensionRequest.query.filter_by(application_id=application.id).all()
    if any(item.status in PENDING_EXTENSION_STATUSES for item in history):
        raise BusinessError("已有待处理延期申请", code=40901, status=409)
    rule = current_extension_rule(application.task_type_id)
    if not rule:
        raise BusinessError("当前任务类型没有可用延期规则", code=40903, status=409)
    request_count = len(history)
    if request_count >= rule.max_extension_requests:
        raise BusinessError("已达到延期申请次数上限", code=40902, status=409)

    attachment_ids = _normalize_id_list(payload.get("attachment_ids"))
    requested_due_at = _parse_datetime(payload.get("requested_due_at"))
    if not requested_due_at:
        raise BusinessError("requested_due_at 不能为空")
    requested_due_at = requested_due_at.replace(microsecond=0)
    if requested_due_at <= business_now():
        raise BusinessError("延期后的成果提交时间必须晚于当前时间")
    if not application.material_due_at or requested_due_at <= application.material_due_at:
        raise BusinessError("延期后的成果提交时间必须晚于原截止时间")
    reason = _required_text(payload, "reason")

    extension_days = ceil((requested_due_at - application.material_due_at).total_seconds() / timedelta(days=1).total_seconds())
    approved_days = sum(item.extension_days for item in history if item.status == "approved")
    projected_days = approved_days + extension_days
    if projected_days > rule.special_max_days:
        raise BusinessError("累计延期超过规则允许的最大天数", code=40904, status=409)
    if not rule.allow_beyond_graduation:
        if not student.expected_graduation_date:
            raise BusinessError("学生预计毕业日期未维护，不能按当前规则提交延期", code=40905, status=409)
        if requested_due_at.date() > student.expected_graduation_date:
            raise BusinessError("延期后的成果提交日期不能晚于预计毕业日期", code=40905, status=409)

    is_special = extension_days > rule.ordinary_max_days or projected_days > rule.special_threshold_days
    review_level = "admin" if is_special else "advisor"
    request_status = "pending_admin_review" if is_special else "pending_advisor_review"
    before = application.status
    application.status = "extension_admin_review" if is_special else "extension_requested"
    application.extension_count = request_count + 1
    submitted_at = business_now()
    extension = ExtensionRequest(
        application_id=application.id,
        old_due_at=application.material_due_at,
        requested_due_at=requested_due_at,
        extension_days=extension_days,
        reason=reason,
        review_level=review_level,
        status=request_status,
        rule_id=rule.id,
        rule_snapshot=extension_rule_snapshot(rule, submitted_at),
        submitted_at=submitted_at,
        approved_extension_days_before=approved_days,
        projected_total_extension_days=projected_days,
    )
    db.session.add(extension)
    db.session.flush()
    _bind_attachments(extension.id, attachment_ids, user.id)
    _add_operation(user.id, extension.id, "request_extension", before, application.status)
    if review_level == "advisor":
        advisor = _primary_advisor(application.id)
        if advisor and advisor.teacher:
            create_notification(
                advisor.teacher.user_id, user.id, "extension", "extension_review_requested",
                "新的延期申请待处理", f"学生为课时申请“{application.title}”提交了延期申请，请及时处理。",
                biz_type="extension_request", biz_id=extension.id,
                payload={"application_id": application.id, "status": extension.status},
                dedupe_key=f"extension:{extension.id}:advisor-review:requested",
            )
    db.session.commit()
    return extension


def get_extension_eligibility(user, application_id):
    student = current_student(user)
    application = _visible_application(student.id, application_id)
    history = ExtensionRequest.query.filter_by(application_id=application.id).all()
    rule = current_extension_rule(application.task_type_id) if application.task_type_id else None
    count = len(history)
    approved_days = sum(item.extension_days for item in history if item.status == "approved")
    can_apply, reason_code, reason = True, None, None
    if application.application_type != "without_material" or application.status != "pending_material":
        can_apply, reason_code, reason = False, 40901, "当前申请状态不允许延期"
    elif any(item.status in PENDING_EXTENSION_STATUSES for item in history):
        can_apply, reason_code, reason = False, 40901, "已有待处理延期申请"
    elif not rule:
        can_apply, reason_code, reason = False, 40903, "当前任务类型没有可用延期规则"
    elif count >= rule.max_extension_requests:
        can_apply, reason_code, reason = False, 40902, "已达到延期申请次数上限"
    elif not rule.allow_beyond_graduation and not student.expected_graduation_date:
        can_apply, reason_code, reason = False, 40905, "学生预计毕业日期未维护"
    return {
        "can_apply": can_apply, "reason_code": reason_code, "reason": reason,
        "application_id": application.id, "current_due_at": application.material_due_at,
        "submitted_request_count": count, "approved_extension_days": approved_days,
        "remaining_request_count": max(rule.max_extension_requests - count, 0) if rule else 0,
        "remaining_extension_days": max(rule.special_max_days - approved_days, 0) if rule else 0,
        "expected_graduation_date": student.expected_graduation_date, "rule": rule,
    }


def list_advisor_pending_extensions(user, page=None, page_size=None):
    teacher = current_teacher(user, "advisor")
    query = ExtensionRequest.query.join(HourApplication).join(ApplicationAdvisor).filter(
        ExtensionRequest.review_level == "advisor",
        ExtensionRequest.status == "pending_advisor_review",
        ApplicationAdvisor.teacher_id == teacher.id,
        ApplicationAdvisor.advisor_role == "primary",
        ApplicationAdvisor.can_operate.is_(True),
    ).order_by(ExtensionRequest.created_at.desc(), ExtensionRequest.id.desc())
    return finish_query(query, page, page_size)


def list_admin_extensions(pending_special=False, page=None, page_size=None):
    query = ExtensionRequest.query
    if pending_special:
        query = query.filter_by(review_level="admin", status="pending_admin_review")
    return finish_query(query.order_by(ExtensionRequest.created_at.desc(), ExtensionRequest.id.desc()), page, page_size)


def get_visible_extension_request(user, extension_request_id):
    extension = db.session.get(ExtensionRequest, extension_request_id)
    if not extension:
        raise BusinessError("延期申请不存在", code=40401, status=404)
    if user.has_role("admin"):
        return extension
    if user.has_role("advisor"):
        teacher = current_teacher(user, "advisor")
        if _primary_advisor(extension.application_id, teacher.id):
            return extension
    if user.has_role("student"):
        student = current_student(user)
        if _student_can_manage(student.id, extension.application):
            return extension
    raise BusinessError("无权查看该延期申请", code=40301, status=403)


def review_extension_request(user, extension_request_id, approve, comment=None, reviewer_role="advisor"):
    extension = ExtensionRequest.query.filter_by(id=extension_request_id).with_for_update().first()
    if not extension:
        raise BusinessError("延期申请不存在", code=40401, status=404)
    application = extension.application
    if reviewer_role == "advisor":
        teacher = current_teacher(user, "advisor")
        if extension.review_level != "advisor" or not _primary_advisor(application.id, teacher.id):
            raise BusinessError("当前指导老师无权处理该延期申请", code=40301, status=403)
        expected_request_status, expected_status, teacher_id = "pending_advisor_review", "extension_requested", teacher.id
    else:
        if not user.has_role("admin") or extension.review_level != "admin":
            raise BusinessError("当前管理员无权处理该延期申请", code=40301, status=403)
        expected_request_status, expected_status, teacher_id = "pending_admin_review", "extension_admin_review", None
    if extension.status != expected_request_status:
        raise BusinessError("该延期申请已经处理", code=40901, status=409)
    _require_status(application, expected_status)
    if not approve and not (comment or "").strip():
        raise BusinessError("驳回原因不能为空")

    before = application.status
    extension.status = "approved" if approve else "rejected"
    extension.reviewed_by = user.id
    extension.review_comment = (comment or "").strip() or None
    extension.reviewed_at = business_now()
    if approve:
        application.material_due_at, application.status = extension.requested_due_at, "pending_material"
        decision = "extension_approved"
    else:
        application.status = "material_overdue" if extension.old_due_at <= business_now() else "pending_material"
        decision = "extension_rejected"
    _add_review(application, user.id, teacher_id, reviewer_role, decision, before, application.status, comment)
    _add_operation(user.id, extension.id, decision, before, application.status)
    recipient = application.leader or application.applicant or application.student
    if recipient:
        create_notification(
            recipient.user_id, user.id, "extension", decision,
            "延期申请已通过" if approve else "延期申请已驳回",
            f"您的延期申请已通过，新的成果截止时间为 {extension.requested_due_at}。" if approve else f"您的延期申请已被驳回。原因：{comment}",
            biz_type="extension_request", biz_id=extension.id,
            payload={"application_id": application.id, "status": extension.status},
            dedupe_key=f"extension:{extension.id}:1:{'approved' if approve else 'rejected'}",
        )
    db.session.commit()
    return extension, decision


def _visible_application(student_id, application_id):
    application = db.session.get(HourApplication, application_id)
    if not application or not _student_can_manage(student_id, application):
        raise BusinessError("课时申请不存在或不可见", code=40401, status=404)
    return application


def _student_can_manage(student_id, application):
    if student_id in {application.student_id, application.applicant_student_id, application.leader_student_id}:
        return True
    return HourApplicationMember.query.filter_by(application_id=application.id, student_id=student_id, status="active").first() is not None


def _primary_advisor(application_id, teacher_id=None):
    query = ApplicationAdvisor.query.filter_by(application_id=application_id, advisor_role="primary", can_operate=True)
    return query.filter_by(teacher_id=teacher_id).first() if teacher_id else query.first()


def _bind_attachments(extension_id, attachment_ids, user_id):
    if not attachment_ids:
        return
    attachments = Attachment.query.filter(Attachment.id.in_(attachment_ids), Attachment.status == "active").all()
    if len(attachments) != len(set(attachment_ids)):
        raise BusinessError("延期附件不存在或无权使用", code=40301, status=403)
    for attachment in attachments:
        if attachment.uploaded_by != user_id or attachment.biz_type not in {"extension_request", "hour_application"}:
            raise BusinessError("延期附件不存在或无权使用", code=40301, status=403)
        if attachment.owner_id:
            raise BusinessError("延期附件已绑定其他业务", code=40902, status=409)
        attachment.owner_type, attachment.owner_id = "extension_request", extension_id


def _add_review(application, user_id, teacher_id, stage, decision, before, after, comment):
    db.session.add(HourApplicationReview(
        application_id=application.id, reviewer_teacher_id=teacher_id,
        operator_user_id=user_id, operator_teacher_id=teacher_id, stage=stage,
        operator_role=stage, decision=decision, action=decision,
        before_status=before, after_status=after,
        requested_hours_snapshot=application.requested_hours,
        comment=(comment or "").strip() or None,
    ))


def _add_operation(user_id, extension_id, action, before, after):
    db.session.add(OperationLog(
        user_id=user_id, module="hour_application", biz_type="extension_request",
        biz_id=extension_id, action=action, detail=f"{before}->{after}",
    ))


def _require_status(application, expected):
    if application.status != expected:
        raise BusinessError("当前状态不允许执行该操作", code=40901, status=409)


def _required_text(payload, key):
    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise BusinessError(f"{key} 不能为空")
    return value.strip()


def _normalize_id_list(value):
    if value is None:
        return []
    if not isinstance(value, list):
        raise BusinessError("ID 列表格式不正确")
    if len(value) > 10:
        raise BusinessError("attachment_ids 最多包含 10 项")
    if any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in value):
        raise BusinessError("ID 列表只能包含正整数")
    if len(set(value)) != len(value):
        raise BusinessError("ID 列表不能包含重复 ID")
    return value


def _parse_datetime(value):
    try:
        return parse_api_datetime(value)
    except (TypeError, ValueError):
        raise BusinessError("时间格式必须是 ISO 8601 字符串")
