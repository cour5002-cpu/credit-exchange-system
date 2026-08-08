from sqlalchemy import and_, or_

from app.core.errors import BusinessError
from app.core.identity import current_student, current_teacher
from app.extensions import db
from app.models.appeal import Appeal
from app.models.application_advisor import ApplicationAdvisor
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.hour_application import HourApplication
from app.models.rule_file import RuleFile
from app.services.appeal_workflow import reconcile_reopened_hour_appeals
from app.services.service_helpers import (
    add_operation as _add_operation,
    bind_attachments as _bind_attachments,
    normalize_id_list as _normalize_id_list,
    required_choice as _required_choice,
    required_int as _required_int,
    required_str as _required_str,
    require_status as _require_status,
)
from app.services.week3_hour_application_service import (
    advisor_approve,
    advisor_reject,
    assign_reviewer,
    prepare_task_result_reconfirmation,
    reviewer_approve,
    reviewer_reject,
)
from app.services.week4_credit_exchange_service import (
    advisor_approve_credit_exchange,
    advisor_reject_credit_exchange,
)
from app.utils.number_generator import generate_application_no
from app.utils.pagination import finish_query
from app.utils.time_utils import business_now


APPEAL_TARGET_TYPES = {"hour_application", "credit_exchange"}
HOUR_APPEALABLE_STATUSES = {
    "reviewer_modified_approved",
    "reviewer_rejected",
    "final_rejected",
    "material_overdue",
}
CREDIT_APPEALABLE_STATUSES = {"final_rejected"}


def create_appeal(user, payload):
    student = current_student(user)
    target_type = _required_choice(
        payload.get("target_type"), APPEAL_TARGET_TYPES, "申诉对象类型不合法"
    )
    target_id = _required_int(payload, "target_id")
    reason = _required_str(payload, "reason")
    target = _get_appeal_target(target_type, target_id)
    _ensure_student_can_appeal(student, target_type, target)
    if Appeal.query.filter_by(target_type=target_type, target_id=target_id).first():
        raise BusinessError("同一业务对象只能申诉一次", code=40902, status=409)
    attachment_ids = _normalize_id_list(payload.get("attachment_ids"))
    if not attachment_ids:
        raise BusinessError("发起申诉必须提交证明附件")
    standard_rule_file_id = payload.get("standard_rule_file_id")
    if standard_rule_file_id:
        standard_rule_file_id = _required_int(payload, "standard_rule_file_id")
        if not RuleFile.query.filter_by(id=standard_rule_file_id, status="active").first():
            raise BusinessError("审核标准文件不存在", code=40401, status=404)

    appeal = Appeal(
        appeal_no=generate_application_no("AP"),
        target_type=target_type,
        target_id=target_id,
        applicant_student_id=student.id,
        reason=reason,
        status="pending_admin_review",
        original_status=target.status,
        standard_rule_file_id=standard_rule_file_id,
    )
    db.session.add(appeal)
    db.session.flush()
    _bind_attachments("appeal", appeal.id, attachment_ids, user.id)
    if target_type == "hour_application":
        target.appeal_id = appeal.id
    _add_operation(user.id, "appeal", appeal.id, "submit", None, appeal.status)
    db.session.commit()
    return appeal


def list_student_appeals(user, status=None, page=None, page_size=None):
    student = current_student(user)
    query = Appeal.query.filter_by(applicant_student_id=student.id)
    if status:
        query = query.filter_by(status=status)
    return finish_query(
        query.order_by(Appeal.created_at.desc(), Appeal.id.desc()),
        page,
        page_size,
    )


def get_student_appeal(user, appeal_id):
    student = current_student(user)
    appeal = Appeal.query.filter_by(id=appeal_id, applicant_student_id=student.id).first()
    if not appeal:
        raise BusinessError("申诉不存在或不可见", code=40401, status=404)
    return appeal


def list_admin_appeals(status=None, page=None, page_size=None):
    reconcile_reopened_hour_appeals()
    query = Appeal.query
    if status:
        query = query.filter_by(status=status)
    return finish_query(
        query.order_by(Appeal.created_at.desc(), Appeal.id.desc()),
        page,
        page_size,
    )


def get_admin_appeal(appeal_id):
    appeal = db.session.get(Appeal, appeal_id)
    if not appeal:
        raise BusinessError("申诉不存在", code=40401, status=404)
    return appeal


def get_appeal_target(appeal):
    return _get_appeal_target(appeal.target_type, appeal.target_id)


def admin_approve_appeal(user, appeal_id, admin_advice):
    if not admin_advice:
        raise BusinessError("管理员认定意见不能为空")
    appeal = get_admin_appeal(appeal_id)
    _require_status(appeal.status, "pending_admin_review")
    target = _get_appeal_target(appeal.target_type, appeal.target_id)
    before = appeal.status
    appeal.status = "processing"
    appeal.reopen_stage = "pending_advisor_confirmation"
    appeal.admin_decision = "reopen"
    appeal.admin_advice = admin_advice
    appeal.reviewed_by = user.id
    appeal.reviewed_at = business_now()
    target_status = "submitted"
    if (
        appeal.target_type == "hour_application"
        and target.application_type == "without_material"
        and appeal.original_status != "material_overdue"
    ):
        target_status = "material_submitted"
    target.status = target_status
    if appeal.target_type == "hour_application":
        target.appeal_advice = admin_advice
        prepare_task_result_reconfirmation(target, user.id)
    _add_operation(user.id, "appeal", appeal.id, "approve", before, appeal.status)
    db.session.commit()
    return appeal, target


def get_appealable_target(user, target_type, target_id):
    student = current_student(user)
    target = _get_appeal_target(target_type, target_id)
    try:
        _ensure_student_can_appeal(student, target_type, target)
    except BusinessError as exc:
        if exc.status == 403:
            raise
        return target, False, str(exc)
    if Appeal.query.filter_by(target_type=target_type, target_id=target_id).first():
        return target, False, "同一业务对象只能申诉一次"
    return target, True, None


def list_reopened_pending_advisor(user, page=None, page_size=None):
    reconcile_reopened_hour_appeals()
    teacher = current_teacher(user, "advisor")
    hour_ids = db.session.query(ApplicationAdvisor.application_id).filter_by(
        teacher_id=teacher.id,
        advisor_role="primary",
        can_operate=True,
    )
    exchange_ids = db.session.query(CreditExchangeApplication.id).filter_by(
        advisor_teacher_id=teacher.id
    )
    query = Appeal.query.filter(
        Appeal.status == "processing",
        Appeal.reopen_stage == "pending_advisor_confirmation",
        or_(
            and_(Appeal.target_type == "hour_application", Appeal.target_id.in_(hour_ids)),
            and_(Appeal.target_type == "credit_exchange", Appeal.target_id.in_(exchange_ids)),
        ),
    ).order_by(Appeal.id.desc())
    return finish_query(query, page, page_size)


def advisor_reconfirm_appeal(user, appeal_id, decision, comment=None):
    appeal = get_admin_appeal(appeal_id)
    if appeal.status != "processing" or appeal.reopen_stage != "pending_advisor_confirmation":
        raise BusinessError("当前申诉不在指导老师再次确认环节", code=40901, status=409)
    if decision not in {"approve", "reject"}:
        raise BusinessError("decision 只能是 approve 或 reject")
    if decision == "reject" and not (comment or "").strip():
        raise BusinessError("再次确认驳回原因不能为空")
    if appeal.target_type == "hour_application":
        target_application = _get_appeal_target("hour_application", appeal.target_id)
        prepare_task_result_reconfirmation(target_application, user.id)
        reuse_submitted_material = (
            target_application.application_type == "without_material"
            and target_application.status == "material_submitted"
        )
        target = (
            advisor_approve(
                user,
                appeal.target_id,
                comment,
                material=reuse_submitted_material,
                appeal_id=appeal.id,
            )
            if decision == "approve"
            else advisor_reject(
                user,
                appeal.target_id,
                comment,
                material=reuse_submitted_material,
                appeal_id=appeal.id,
            )
        )
        appeal.reopen_stage = "pending_assignment" if decision == "approve" else "advisor_rejected"
    else:
        target = (
            advisor_approve_credit_exchange(user, appeal.target_id, comment)
            if decision == "approve"
            else advisor_reject_credit_exchange(user, appeal.target_id, comment)
        )
        appeal.reopen_stage = "pending_admin_final" if decision == "approve" else "advisor_rejected"
    if decision == "reject":
        appeal.status = "completed"
    appeal.reconfirmed_by = user.id
    appeal.reconfirmed_at = business_now()
    _add_operation(
        user.id,
        "appeal",
        appeal.id,
        f"advisor_reconfirm_{decision}",
        "pending_advisor_confirmation",
        appeal.reopen_stage,
    )
    db.session.commit()
    return appeal, target


def list_reopened_pending_assignment(page=None, page_size=None):
    reconcile_reopened_hour_appeals()
    query = Appeal.query.filter_by(
        status="processing",
        reopen_stage="pending_assignment",
    ).order_by(Appeal.id.desc())
    return finish_query(query, page, page_size)


def assign_reopened_appeal(user, appeal_id, reviewer_teacher_id, comment=None):
    appeal = get_admin_appeal(appeal_id)
    if appeal.target_type != "hour_application" or appeal.reopen_stage != "pending_assignment":
        raise BusinessError("当前申诉不允许分配审核老师", code=40901, status=409)
    target = assign_reviewer(
        user,
        appeal.target_id,
        reviewer_teacher_id,
        comment,
        appeal_id=appeal.id,
    )
    appeal.reopen_stage = "pending_reviewer_review"
    _add_operation(
        user.id, "appeal", appeal.id, "assign_reviewer", "pending_assignment", appeal.reopen_stage
    )
    db.session.commit()
    return appeal, target


def list_reviewer_appeals(user, page=None, page_size=None):
    reconcile_reopened_hour_appeals()
    teacher = current_teacher(user, "reviewer")
    query = (
        Appeal.query.join(HourApplication, HourApplication.id == Appeal.target_id)
        .filter(
            Appeal.target_type == "hour_application",
            Appeal.status == "processing",
            Appeal.reopen_stage == "pending_reviewer_review",
            HourApplication.assigned_teacher_id == teacher.id,
            HourApplication.status == "pending_review",
        )
        .order_by(Appeal.id.desc())
    )
    return finish_query(query, page, page_size)


def get_reviewer_appeal(user, appeal_id):
    items = {item.id: item for item in list_reviewer_appeals(user)}
    if appeal_id not in items:
        raise BusinessError("申诉复审任务不存在或未分配给当前审核老师", code=40401, status=404)
    return items[appeal_id]


def review_reopened_appeal(
    user,
    appeal_id,
    decision,
    comment=None,
    suggested_hours=None,
):
    appeal = get_reviewer_appeal(user, appeal_id)
    if decision == "approve":
        target, _ = reviewer_approve(
            user,
            appeal.target_id,
            comment,
            appeal_id=appeal.id,
        )
    elif decision == "modified_approve":
        target, _ = reviewer_approve(
            user,
            appeal.target_id,
            comment,
            suggested_hours,
            modified=True,
            appeal_id=appeal.id,
        )
    elif decision == "reject":
        target = reviewer_reject(
            user,
            appeal.target_id,
            comment,
            appeal_id=appeal.id,
        )
    else:
        raise BusinessError("复审决定不合法")
    appeal.reopen_stage = "pending_admin_final" if decision != "reject" else "reviewer_rejected"
    if decision == "reject":
        appeal.status = "completed"
    _add_operation(
        user.id,
        "appeal",
        appeal.id,
        f"reviewer_{decision}",
        "pending_reviewer_review",
        appeal.reopen_stage,
    )
    db.session.commit()
    return appeal, target


def admin_reject_appeal(user, appeal_id, admin_advice):
    if not admin_advice:
        raise BusinessError("驳回依据不能为空")
    appeal = get_admin_appeal(appeal_id)
    _require_status(appeal.status, "pending_admin_review")
    before = appeal.status
    appeal.status = "completed"
    appeal.admin_decision = "maintain"
    appeal.admin_advice = admin_advice
    appeal.reviewed_by = user.id
    appeal.reviewed_at = business_now()
    _add_operation(user.id, "appeal", appeal.id, "reject", before, appeal.status)
    db.session.commit()
    return appeal


def _get_appeal_target(target_type, target_id):
    if target_type == "hour_application":
        target = db.session.get(HourApplication, target_id)
    elif target_type == "credit_exchange":
        target = db.session.get(CreditExchangeApplication, target_id)
    else:
        target = None
    if not target:
        raise BusinessError("申诉对象不存在", code=40401, status=404)
    return target


def _ensure_student_can_appeal(student, target_type, target):
    if target_type == "hour_application":
        if target.status not in HOUR_APPEALABLE_STATUSES:
            raise BusinessError("当前课时申请状态不可申诉", code=40901, status=409)
        if target.status == "final_approved":
            raise BusinessError("终审通过后不可再次申诉", code=40901, status=409)
        if target.applicant_student_id != student.id and target.student_id != student.id:
            raise BusinessError("只能申诉自己发起的课时申请", code=40301, status=403)
        return
    if target.status not in CREDIT_APPEALABLE_STATUSES:
        raise BusinessError("当前学分兑换状态不可申诉", code=40901, status=409)
    if target.applicant_student_id != student.id and target.student_id != student.id:
        raise BusinessError("只能申诉自己发起的学分兑换", code=40301, status=403)
