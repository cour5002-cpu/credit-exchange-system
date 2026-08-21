from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation

from sqlalchemy import or_

from app.core.errors import BusinessError
from app.core.identity import current_student, current_teacher
from app.extensions import db
from app.models.application_advisor import ApplicationAdvisor
from app.models.attachment import Attachment
from app.models.extension_request import ExtensionRequest
from app.models.hour_application import HourApplication
from app.models.hour_application_attachment import HourApplicationAttachment
from app.models.hour_application_member import HourApplicationMember
from app.models.hour_application_review import HourApplicationReview
from app.models.hour_award_record import HourAwardRecord
from app.models.operation_log import OperationLog
from app.models.review_assignment import ReviewAssignment
from app.models.student import Student
from app.models.task_type import TaskType
from app.models.task_result_submission import TaskResultSubmission
from app.models.teacher import Teacher
from app.services.appeal_workflow import (
    exclude_active_reopened_appeals,
    require_hour_application_workflow,
)
from app.services.hour_account_service import add_hours
from app.services.notification_service import create_notification
from app.services.extension_rule_service import current_extension_rule
from app.services.extension_request_service import (
    create_extension_request,
    get_extension_eligibility as extension_eligibility,
    get_visible_extension_request,
    list_admin_extensions,
    list_advisor_pending_extensions,
    review_extension_request,
)
from app.utils.number_generator import generate_application_no
from app.utils.pagination import finish_query
from app.utils.time_utils import business_now, parse_api_datetime


VALID_APPLICATION_TYPES = {"with_material", "without_material", "task_result"}
VALID_SOURCE_TYPES = {"student_self", "admin_task", "teacher_task"}
EXTENSION_CLOSABLE_STATUSES = {
    "pending_material",
    "extension_requested",
    "extension_admin_review",
    "extension_rejected",
    "material_overdue",
}
EXTENSION_PENDING_STATUSES = {
    "pending_advisor_review",
    "pending_admin_review",
}


def create_student_application(user, payload, submit=True):
    student = current_student(user)
    application_type = _required_str(payload, "application_type")
    if application_type not in VALID_APPLICATION_TYPES:
        raise BusinessError("申请类型只能是 with_material、without_material 或 task_result")
    if application_type == "task_result":
        raise BusinessError("任务成果认定由学院任务成果流程生成，学生自主申请暂不直接提交 task_result")

    source_type = payload.get("source_type") or "student_self"
    if source_type not in VALID_SOURCE_TYPES:
        raise BusinessError("任务来源不合法")
    if source_type != "student_self":
        raise BusinessError("第3周只实现学生自主申请入口，学院任务来源在第5周实现")

    task_type = _enabled_task_type(payload.get("task_type_id"), source_type)
    requested_hours = _positive_decimal(payload.get("requested_hours"), "申请课时必须大于 0")
    title = _required_str(payload, "title")
    advisor_teacher_id = _required_int(payload, "advisor_teacher_id")
    primary_advisor = _active_teacher_with_flag(advisor_teacher_id, "advisor")
    view_teacher_ids = _normalize_id_list(payload.get("view_teacher_ids"))
    if advisor_teacher_id in view_teacher_ids:
        raise BusinessError("主指导老师不能重复作为查看导师")
    if len(view_teacher_ids) + 1 > 3:
        raise BusinessError("导师总人数最多 3 人")
    view_teachers = [_active_teacher_with_flag(teacher_id, "advisor") for teacher_id in view_teacher_ids]

    material_due_at = _parse_datetime(payload.get("material_due_at"))
    if application_type == "without_material":
        if not material_due_at and submit:
            rule = current_extension_rule(task_type.id)
            if rule:
                material_due_at = business_now() + timedelta(days=rule.default_material_due_days)
        if not material_due_at and submit:
            raise BusinessError("无成果申请必须填写成果提交时间")
        if submit and material_due_at <= business_now():
            raise BusinessError("成果提交时间不能早于当前时间")

    member_ids = _normalize_id_list(payload.get("member_student_ids"))
    member_count = payload.get("member_count")
    if member_count is not None:
        try:
            member_count = int(member_count)
        except (TypeError, ValueError):
            raise BusinessError("参与人数必须是整数")
    if not member_ids:
        member_ids = [student.id]
    if student.id not in member_ids:
        member_ids.insert(0, student.id)
    if member_count and member_count >= 2 and len(member_ids) < 2:
        raise BusinessError("多人申请必须填写参与学生")
    if member_count and member_count != len(member_ids):
        raise BusinessError("参与人数与成员数量不一致")

    leader_student_id = payload.get("leader_student_id")
    if leader_student_id is None:
        leader_student_id = student.id if len(member_ids) == 1 else None
    leader_student_id = _required_int({"leader_student_id": leader_student_id}, "leader_student_id")
    if leader_student_id not in member_ids:
        raise BusinessError("队长必须在参与成员中")
    students = _active_students(member_ids)
    if len(students) != len(set(member_ids)):
        raise BusinessError("参与成员必须是系统内有效学生")

    attachment_ids = _normalize_id_list(payload.get("attachment_ids"))
    if application_type == "with_material" and submit and not attachment_ids:
        # The standalone attachment API is not part of this backend slice yet. Keep
        # the field validation soft at binding time, but still require the caller to
        # declare at least one material id for API-contract alignment.
        raise BusinessError("有成果申请必须提供成果附件 ID")

    application = HourApplication(
        application_no=generate_application_no("HS"),
        student_id=student.id,
        applicant_student_id=student.id,
        leader_student_id=leader_student_id,
        application_type=application_type,
        source_type=source_type,
        task_type_id=task_type.id,
        task_type_code=task_type.type_code,
        title=title,
        major_name=payload.get("major_name") or student.major or "",
        course_name=payload.get("course_name") or "",
        requested_hours=requested_hours,
        achievement_summary=(payload.get("achievement_summary") or "").strip() or None,
        description=(payload.get("description") or "").strip() or None,
        material_due_at=material_due_at,
        status="submitted" if submit else "draft",
        submitted_at=business_now() if submit else None,
    )
    db.session.add(application)
    db.session.flush()

    for item in students:
        db.session.add(
            HourApplicationMember(
                application_id=application.id,
                student_id=item.id,
                is_leader=item.id == leader_student_id,
                can_view=True,
                can_apply_credit_exchange=item.id == leader_student_id,
            )
        )

    db.session.add(
        ApplicationAdvisor(
            application_id=application.id,
            teacher_id=primary_advisor.id,
            advisor_role="primary",
            can_operate=True,
        )
    )
    for teacher in view_teachers:
        db.session.add(
            ApplicationAdvisor(
                application_id=application.id,
                teacher_id=teacher.id,
                advisor_role="viewer",
                can_operate=False,
            )
        )

    _bind_legacy_attachments(application.id, attachment_ids, user.id)
    if submit:
        create_notification(
            primary_advisor.user_id,
            user.id,
            "hour_application",
            "hour_application_submitted",
            "新的课时申请待确认",
            f"学生{student.name}提交了课时申请“{application.title}”，请及时确认。",
            biz_type="hour_application",
            biz_id=application.id,
            payload={"application_no": application.application_no, "status": application.status},
            dedupe_key=f"hour-application:{application.id}:submitted:initial",
        )
    db.session.commit()
    return application


def list_student_hour_applications(user, status=None, role=None, page=None, page_size=None):
    student = current_student(user)
    query = HourApplication.query.outerjoin(
        HourApplicationMember,
        HourApplicationMember.application_id == HourApplication.id,
    ).filter(
        or_(
            HourApplication.applicant_student_id == student.id,
            HourApplication.student_id == student.id,
            HourApplicationMember.student_id == student.id,
        )
    )
    if status:
        query = query.filter(HourApplication.status == status)
    if role == "applicant":
        query = query.filter(or_(HourApplication.applicant_student_id == student.id, HourApplication.student_id == student.id))
    elif role == "member":
        query = query.filter(HourApplicationMember.student_id == student.id)
    query = query.order_by(HourApplication.created_at.desc(), HourApplication.id.desc()).distinct()
    return finish_query(query, page, page_size)


def list_admin_hour_applications(status=None, application_type=None, keyword=None, page=None, page_size=None):
    query = HourApplication.query
    if status:
        query = query.filter_by(status=status)
    if application_type:
        query = query.filter_by(application_type=application_type)
    if keyword:
        like = f"%{keyword}%"
        query = query.outerjoin(Student, Student.id == HourApplication.applicant_student_id).filter(
            or_(
                HourApplication.title.like(like),
                HourApplication.application_no.like(like),
                Student.name.like(like),
                Student.student_no.like(like),
            )
        )
    query = query.order_by(HourApplication.created_at.desc(), HourApplication.id.desc())
    return finish_query(query, page, page_size)


def get_visible_application_for_student(user, application_id):
    items = list_student_hour_applications(user)
    for item in items:
        if item.id == application_id:
            return item
    raise BusinessError("课时申请不存在或不可见", code=40401, status=404)


def close_unfinishable_application(user, application_id, reason):
    reason = (reason or "").strip()
    if not reason:
        raise BusinessError("关闭原因不能为空")
    application = get_application(application_id)
    if application.application_type != "without_material" or application.status not in EXTENSION_CLOSABLE_STATUSES:
        raise BusinessError("当前状态不允许终止并关闭", code=40901, status=409)
    before = application.status
    application.status = "closed"
    for extension in application.extension_requests:
        if extension.status in EXTENSION_PENDING_STATUSES:
            extension.status = "closed"
            extension.reviewed_by = user.id
            extension.review_comment = reason
            extension.reviewed_at = business_now()
    _add_review(application, user.id, None, "admin", "closed", before, application.status, reason)
    _add_operation(user.id, "hour_application", application.id, "close_unfinishable", before, application.status)
    db.session.commit()
    return application


def list_advisor_pending(user, status="submitted", page=None, page_size=None):
    teacher = current_teacher(user, "advisor")
    query = exclude_active_reopened_appeals(_advisor_query(teacher, status))
    query = query.order_by(HourApplication.created_at.desc(), HourApplication.id.desc())
    return finish_query(query, page, page_size)


def list_advisor_material_pending(user, page=None, page_size=None):
    teacher = current_teacher(user, "advisor")
    query = exclude_active_reopened_appeals(_advisor_query(teacher, "material_submitted")).filter(
        HourApplication.application_type == "without_material"
    ).order_by(HourApplication.created_at.desc(), HourApplication.id.desc())
    return finish_query(query, page, page_size)


def get_application(application_id):
    application = db.session.get(HourApplication, application_id)
    if not application:
        raise BusinessError("课时申请不存在", code=40401, status=404)
    return application


def get_advisor_application(user, application_id):
    teacher = current_teacher(user, "advisor")
    application = get_application(application_id)
    if not _is_primary_advisor(application.id, teacher.id):
        raise BusinessError("当前教师不是该申请的主指导老师", code=40301, status=403)
    return application


def get_advisor_material_application(user, application_id):
    application = get_advisor_application(user, application_id)
    if application.application_type != "without_material":
        raise BusinessError(
            "该记录不是无成果补交申请，请使用任务成果确认接口",
            code=40901,
            status=409,
        )
    return application


def advisor_approve(user, application_id, comment=None, material=False, appeal_id=None):
    teacher = current_teacher(user, "advisor")
    application = get_application(application_id)
    if not _is_primary_advisor(application.id, teacher.id):
        raise BusinessError("当前教师不是该申请的主指导老师", code=40301, status=403)
    require_hour_application_workflow(application.id, appeal_id)
    if material and application.application_type != "without_material":
        raise BusinessError(
            "任务成果不能通过补交成果接口确认，请使用任务成果确认接口",
            code=40901,
            status=409,
        )
    expected_status = "material_submitted" if material else "submitted"
    _require_status(application, expected_status)
    before = application.status
    if material:
        application.status = "pending_assignment"
    elif application.application_type == "without_material":
        application.status = "pending_material"
    else:
        application.status = "pending_assignment"
    application.advisor_reviewed_at = business_now()
    _mark_advisor_reviewed(application.id, teacher.id)
    _add_review(application, user.id, teacher.id, "advisor", "approved", before, application.status, comment)
    _sync_task_result_advisor_decision(application, user.id, approved=True, comment=comment)
    recipient = application.leader or application.applicant or application.student
    review_round = HourApplicationReview.query.filter_by(application_id=application.id, stage="advisor").count()
    if recipient:
        create_notification(
            recipient.user_id,
            user.id,
            "hour_application",
            "hour_application_advisor_approved",
            "指导老师已确认课时申请",
            f"您的课时申请“{application.title}”已由指导老师确认，当前状态：{application.status_name}。",
            biz_type="hour_application",
            biz_id=application.id,
            payload={"application_no": application.application_no, "status": application.status},
            dedupe_key=f"hour-application:{application.id}:{review_round}:advisor:approved",
        )
    db.session.commit()
    return application


def advisor_reject(user, application_id, comment, material=False, appeal_id=None):
    if not comment:
        raise BusinessError("驳回原因不能为空")
    teacher = current_teacher(user, "advisor")
    application = get_application(application_id)
    if not _is_primary_advisor(application.id, teacher.id):
        raise BusinessError("当前教师不是该申请的主指导老师", code=40301, status=403)
    require_hour_application_workflow(application.id, appeal_id)
    if material and application.application_type != "without_material":
        raise BusinessError(
            "任务成果不能通过补交成果接口驳回，请使用任务成果确认接口",
            code=40901,
            status=409,
        )
    expected_status = "material_submitted" if material else "submitted"
    _require_status(application, expected_status)
    before = application.status
    application.status = "advisor_rejected"
    application.advisor_reviewed_at = business_now()
    _mark_advisor_reviewed(application.id, teacher.id)
    _add_review(application, user.id, teacher.id, "advisor", "rejected", before, application.status, comment)
    _sync_task_result_advisor_decision(application, user.id, approved=False, comment=comment)
    recipient = application.leader or application.applicant or application.student
    review_round = HourApplicationReview.query.filter_by(application_id=application.id, stage="advisor").count()
    if recipient:
        create_notification(
            recipient.user_id,
            user.id,
            "hour_application",
            "hour_application_advisor_rejected",
            "指导老师驳回课时申请",
            f"您的课时申请“{application.title}”已被指导老师驳回。原因：{comment}",
            biz_type="hour_application",
            biz_id=application.id,
            payload={"application_no": application.application_no, "status": application.status},
            dedupe_key=f"hour-application:{application.id}:{review_round}:advisor:rejected",
        )
    db.session.commit()
    return application


def prepare_task_result_reconfirmation(application, user_id):
    """Restore a task-result application to the advisor confirmation state."""
    if application.application_type != "task_result":
        return

    submission = None
    if application.task_result_submission_id:
        submission = db.session.get(
            TaskResultSubmission,
            application.task_result_submission_id,
        )
    if not submission:
        submission = TaskResultSubmission.query.filter_by(
            hour_application_id=application.id
        ).first()
    if not submission:
        raise BusinessError(
            "任务成果关联记录不存在，无法重新进入指导老师确认",
            code=40902,
            status=409,
        )

    before = submission.status
    submission.status = "submitted"
    submission.advisor_comment = None
    submission.advisor_reviewed_by = None
    submission.advisor_reviewed_at = None
    application.advisor_reviewed_at = None

    primary_advisor = ApplicationAdvisor.query.filter_by(
        application_id=application.id,
        advisor_role="primary",
        can_operate=True,
    ).first()
    if primary_advisor:
        primary_advisor.reviewed_at = None
    if submission.task:
        submission.task.status = "result_submitted"

    if before != submission.status:
        _add_operation(
            user_id,
            "task_result",
            submission.id,
            "appeal_reopen",
            before,
            submission.status,
        )


def submit_materials(user, application_id, payload):
    student = current_student(user)
    application = get_visible_application_for_student(user, application_id)
    if application.leader_student_id != student.id and application.applicant_student_id != student.id:
        raise BusinessError("只有申请发起人或队长可以补交成果", code=40301, status=403)
    _require_status(application, "pending_material")
    before = application.status
    application.achievement_summary = (payload.get("achievement_summary") or application.achievement_summary or "").strip() or None
    application.status = "material_submitted"
    _bind_legacy_attachments(application.id, _normalize_id_list(payload.get("attachment_ids")), user.id)
    _add_operation(user.id, "hour_application", application.id, "submit_materials", before, application.status)
    primary_advisor = ApplicationAdvisor.query.filter_by(
        application_id=application.id,
        advisor_role="primary",
        can_operate=True,
    ).first()
    if primary_advisor and primary_advisor.teacher:
        create_notification(
            primary_advisor.teacher.user_id, user.id, "hour_application", "hour_application_material_submitted",
            "补交成果待确认",
            f"学生已补交课时申请“{application.title}”的成果，请及时确认。",
            biz_type="hour_application", biz_id=application.id,
            payload={"application_no": application.application_no, "status": application.status},
            dedupe_key=f"hour-application:{application.id}:material:submitted",
        )
    db.session.commit()
    return application


def list_pending_assignment(page=None, page_size=None):
    query = HourApplication.query.filter_by(status="pending_assignment")
    query = exclude_active_reopened_appeals(query)
    query = query.order_by(HourApplication.created_at.desc(), HourApplication.id.desc())
    return finish_query(query, page, page_size)


def assign_reviewer(user, application_id, reviewer_teacher_id, comment=None, appeal_id=None, commit=True):
    application = get_application(application_id)
    require_hour_application_workflow(application.id, appeal_id)
    _require_status(application, "pending_assignment")
    reviewer = _active_teacher_with_flag(reviewer_teacher_id, "reviewer")
    ReviewAssignment.query.filter_by(application_id=application.id, status="active").update({"status": "replaced"})
    before = application.status
    application.assigned_teacher_id = reviewer.id
    application.status = "pending_review"
    db.session.add(
        ReviewAssignment(
            application_id=application.id,
            reviewer_teacher_id=reviewer.id,
            assigned_by=user.id,
            assign_reason=(comment or "").strip() or None,
        )
    )
    _add_operation(user.id, "hour_application", application.id, "assign_reviewer", before, application.status)
    assignment_round = ReviewAssignment.query.filter_by(application_id=application.id).count()
    create_notification(
        reviewer.user_id, user.id, "hour_application", "hour_application_review_assigned",
        "新的课时审核任务",
        f"课时申请“{application.title}”已分配给您审核。",
        biz_type="hour_application", biz_id=application.id,
        payload={"application_no": application.application_no, "status": application.status},
        dedupe_key=f"hour-application:{application.id}:{assignment_round}:review:assigned",
    )
    if commit:
        db.session.commit()
    return application


def list_reviewer_pending(user, page=None, page_size=None):
    teacher = current_teacher(user, "reviewer")
    query = exclude_active_reopened_appeals(
        HourApplication.query.join(ReviewAssignment, ReviewAssignment.application_id == HourApplication.id)
        .filter(
            HourApplication.status == "pending_review",
            ReviewAssignment.reviewer_teacher_id == teacher.id,
            ReviewAssignment.status == "active",
        )
    )
    query = query.order_by(HourApplication.created_at.desc(), HourApplication.id.desc())
    return finish_query(query, page, page_size)


def get_reviewer_application(user, application_id):
    teacher = current_teacher(user, "reviewer")
    application = get_application(application_id)
    if not _is_active_reviewer(application.id, teacher.id):
        raise BusinessError("当前教师不是被分配的审核老师", code=40301, status=403)
    return application


def reviewer_approve(
    user,
    application_id,
    comment=None,
    suggested_hours=None,
    modified=False,
    appeal_id=None,
):
    teacher = current_teacher(user, "reviewer")
    application = get_application(application_id)
    if not _is_active_reviewer(application.id, teacher.id):
        raise BusinessError("当前教师不是被分配的审核老师", code=40301, status=403)
    require_hour_application_workflow(application.id, appeal_id)
    _require_status(application, "pending_review")
    before = application.status
    if modified:
        if not comment:
            raise BusinessError("修改说明不能为空")
        hours = _positive_decimal(suggested_hours, "审核老师建议课时必须大于 0")
        application.reviewer_suggested_hours = hours
        decision = "modified_approved"
        review_status = "reviewer_modified_approved"
    else:
        application.reviewer_suggested_hours = Decimal(str(application.requested_hours))
        decision = "approved"
        review_status = "reviewer_approved"
    application.status = "pending_admin_final"
    application.reviewer_reviewed_at = business_now()
    _add_review(application, user.id, teacher.id, "reviewer", decision, before, application.status, comment, application.reviewer_suggested_hours)
    _add_operation(user.id, "hour_application", application.id, review_status, before, application.status)
    db.session.commit()
    return application, review_status


def reviewer_reject(user, application_id, comment, appeal_id=None):
    if not comment:
        raise BusinessError("驳回原因不能为空")
    teacher = current_teacher(user, "reviewer")
    application = get_application(application_id)
    if not _is_active_reviewer(application.id, teacher.id):
        raise BusinessError("当前教师不是被分配的审核老师", code=40301, status=403)
    require_hour_application_workflow(application.id, appeal_id)
    _require_status(application, "pending_review")
    before = application.status
    application.status = "reviewer_rejected"
    application.reviewer_reviewed_at = business_now()
    _add_review(application, user.id, teacher.id, "reviewer", "rejected", before, application.status, comment)
    _add_operation(user.id, "hour_application", application.id, "reviewer_rejected", before, application.status)
    db.session.commit()
    return application


def list_pending_final(page=None, page_size=None):
    query = HourApplication.query.filter_by(status="pending_admin_final")
    query = exclude_active_reopened_appeals(query)
    query = query.order_by(HourApplication.created_at.desc(), HourApplication.id.desc())
    return finish_query(query, page, page_size)


def final_approve(user, application_id, final_hours=None, comment=None):
    from app.services.appeal_lifecycle import complete_appeal_for_target

    application = get_application(application_id)
    _require_status(application, "pending_admin_final")
    existing = HourAwardRecord.query.filter_by(application_id=application.id).first()
    if existing:
        raise BusinessError("该申请已经生成课时到账记录", code=40902, status=409)
    hours = _positive_decimal(final_hours, "最终确认课时必须大于 0") if final_hours is not None else None
    if hours is None:
        hours = Decimal(str(application.reviewer_suggested_hours or application.requested_hours))
    before = application.status
    application.final_hours = hours
    application.status = "final_approved"
    application.final_reviewed_at = business_now()
    award = HourAwardRecord(
        application_id=application.id,
        leader_student_id=application.leader_student_id or application.applicant_student_id or application.student_id,
        total_hours=hours,
        source_type=application.source_type or "student_self",
        awarded_by=user.id,
        remark=(comment or "").strip() or None,
    )
    db.session.add(award)
    db.session.flush()
    add_hours(award.leader_student_id, hours, "hour_application", application.id, user.id, "课时申请最终确认到账")
    _add_review(application, user.id, None, "admin_final", "approved", before, application.status, comment, hours)
    _add_operation(user.id, "hour_application", application.id, "final_approved", before, application.status)
    complete_appeal_for_target("hour_application", application.id, "completed", user.id)
    for recipient_user_id in _application_recipient_user_ids(application, all_members=True):
        create_notification(
            recipient_user_id, user.id, "hour_application", "hour_application_final_approved",
            "课时申请终审通过",
            f"您的课时申请“{application.title}”已终审通过，确认课时为 {hours}。",
            biz_type="hour_application", biz_id=application.id,
            payload={"application_no": application.application_no, "status": application.status, "final_hours": str(hours)},
            dedupe_key=f"hour-application:{application.id}:final:approved",
        )
    db.session.commit()
    return application, award


def final_reject(user, application_id, comment):
    from app.services.appeal_lifecycle import complete_appeal_for_target

    if not comment:
        raise BusinessError("最终驳回原因不能为空")
    application = get_application(application_id)
    _require_status(application, "pending_admin_final")
    before = application.status
    application.status = "final_rejected"
    application.final_reviewed_at = business_now()
    _add_review(application, user.id, None, "admin_final", "rejected", before, application.status, comment)
    _add_operation(user.id, "hour_application", application.id, "final_rejected", before, application.status)
    complete_appeal_for_target("hour_application", application.id, "completed", user.id)
    for recipient_user_id in _application_recipient_user_ids(application, all_members=True):
        create_notification(
            recipient_user_id, user.id, "hour_application", "hour_application_final_rejected",
            "课时申请终审驳回",
            f"您的课时申请“{application.title}”未通过终审。原因：{comment}",
            biz_type="hour_application", biz_id=application.id,
            payload={"application_no": application.application_no, "status": application.status},
            dedupe_key=f"hour-application:{application.id}:final:rejected",
        )
    db.session.commit()
    return application


def latest_reviewer_result(application_id):
    return (
        HourApplicationReview.query.filter_by(application_id=application_id, stage="reviewer")
        .order_by(HourApplicationReview.created_at.desc(), HourApplicationReview.id.desc())
        .first()
    )


def _advisor_query(teacher, status):
    return (
        HourApplication.query.join(ApplicationAdvisor, ApplicationAdvisor.application_id == HourApplication.id)
        .filter(
            ApplicationAdvisor.teacher_id == teacher.id,
            ApplicationAdvisor.can_operate.is_(True),
            HourApplication.status == status,
        )
    )


def _enabled_task_type(task_type_id, source_type):
    task_type_id = _required_int({"task_type_id": task_type_id}, "task_type_id")
    task_type = TaskType.query.filter_by(id=task_type_id, status="enabled").first()
    if not task_type:
        raise BusinessError("任务类别不存在或未启用")
    if source_type == "student_self" and not task_type.allow_student_self:
        raise BusinessError("该任务类别不允许学生自主申请")
    return task_type


def _active_teacher_with_flag(teacher_id, flag):
    teacher = Teacher.query.filter_by(id=teacher_id, status="active").first()
    if not teacher or flag not in teacher.role_flag_list:
        raise BusinessError("教师不存在或不具备所需角色")
    return teacher


def _active_students(student_ids):
    return Student.query.filter(Student.id.in_(list(set(student_ids))), Student.status == "active").all()


def _is_primary_advisor(application_id, teacher_id):
    return (
        ApplicationAdvisor.query.filter_by(
            application_id=application_id,
            teacher_id=teacher_id,
            advisor_role="primary",
            can_operate=True,
        ).first()
        is not None
    )


def _is_active_reviewer(application_id, teacher_id):
    return (
        ReviewAssignment.query.filter_by(
            application_id=application_id,
            reviewer_teacher_id=teacher_id,
            status="active",
        ).first()
        is not None
    )


def _mark_advisor_reviewed(application_id, teacher_id):
    link = ApplicationAdvisor.query.filter_by(application_id=application_id, teacher_id=teacher_id, advisor_role="primary").first()
    if link:
        link.reviewed_at = business_now()


def _sync_task_result_advisor_decision(application, user_id, approved, comment=None):
    if application.application_type != "task_result":
        return
    submission = TaskResultSubmission.query.filter_by(hour_application_id=application.id).first()
    if not submission:
        raise BusinessError("任务成果关联记录不存在，无法同步确认状态", code=40902, status=409)
    if submission.status != "submitted":
        raise BusinessError("任务成果当前状态不允许指导老师确认", code=40901, status=409)

    before = submission.status
    submission.status = "converted_to_hour_application" if approved else "advisor_rejected"
    submission.advisor_comment = (comment or "").strip() or None
    submission.advisor_reviewed_by = user_id
    submission.advisor_reviewed_at = application.advisor_reviewed_at
    submission.task.status = "result_approved" if approved else "task_in_progress"
    db.session.add(
        OperationLog(
            user_id=user_id,
            module="week5",
            biz_type="task_result",
            biz_id=submission.id,
            action="approve" if approved else "reject",
            detail=f"{before}->{submission.status}",
        )
    )


def _application_recipient_user_ids(application, all_members=False):
    if all_members and len(application.member_links) > 1:
        return sorted({
            link.student.user_id for link in application.member_links
            if link.status == "active" and link.student and link.student.status == "active"
        })
    recipient = application.leader or application.applicant or application.student
    return [recipient.user_id] if recipient else []


def _bind_legacy_attachments(application_id, attachment_ids, user_id):
    if not attachment_ids:
        return
    attachments = Attachment.query.filter(Attachment.id.in_(attachment_ids), Attachment.status == "active").all()
    if len(attachments) != len(set(attachment_ids)):
        raise BusinessError("附件不存在或无权使用", code=40301, status=403)
    for attachment in attachments:
        if attachment.uploaded_by != user_id or attachment.biz_type not in {"hour_application", "task_result"}:
            raise BusinessError("附件不存在或无权使用", code=40301, status=403)
        if attachment.owner_id and attachment.owner_id != application_id:
            raise BusinessError("附件已绑定其他业务", code=40902, status=409)
        attachment.owner_type = "hour_application"
        attachment.owner_id = application_id


def _add_review(application, user_id, teacher_id, stage, decision, before_status, after_status, comment=None, approved_hours=None):
    db.session.add(
        HourApplicationReview(
            application_id=application.id,
            reviewer_teacher_id=teacher_id,
            operator_user_id=user_id,
            operator_teacher_id=teacher_id,
            stage=stage,
            operator_role=stage,
            decision=decision,
            action=decision,
            before_status=before_status,
            after_status=after_status,
            requested_hours_snapshot=application.requested_hours,
            approved_hours=approved_hours,
            comment=(comment or "").strip() or None,
        )
    )


def _add_operation(user_id, biz_type, biz_id, action, before_status, after_status):
    db.session.add(
        OperationLog(
            user_id=user_id,
            module="hour_application",
            biz_type=biz_type,
            biz_id=biz_id,
            action=action,
            detail=f"{before_status}->{after_status}",
        )
    )


def _require_status(application, expected_status):
    if application.status != expected_status:
        raise BusinessError("当前状态不允许执行该操作", code=40901, status=409)


def _required_str(payload, key):
    value = (payload.get(key) or "").strip()
    if not value:
        raise BusinessError(f"{key} 不能为空")
    return value


def _required_int(payload, key):
    value = payload.get(key)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise BusinessError(f"{key} 必须是整数")
    if value <= 0:
        raise BusinessError(f"{key} 必须大于 0")
    return value


def _positive_decimal(value, message):
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise BusinessError(message)
    if number <= 0:
        raise BusinessError(message)
    return number


def _normalize_id_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        value = [item.strip() for item in value.split(",") if item.strip()]
    if not isinstance(value, (list, tuple, set)):
        raise BusinessError("ID 列表格式不正确")
    ids = []
    for item in value:
        try:
            item_id = int(item)
        except (TypeError, ValueError):
            raise BusinessError("ID 列表只能包含整数")
        if item_id <= 0:
            raise BusinessError("ID 列表只能包含正整数")
        if item_id not in ids:
            ids.append(item_id)
    return ids


def _parse_datetime(value):
    try:
        return parse_api_datetime(value)
    except (TypeError, ValueError):
        raise BusinessError("时间格式必须是 ISO 8601 字符串")
