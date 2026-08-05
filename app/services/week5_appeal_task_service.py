from datetime import datetime
from decimal import Decimal, InvalidOperation

from sqlalchemy import and_, or_

from app.extensions import db
from app.models.appeal import Appeal
from app.models.application_advisor import ApplicationAdvisor
from app.models.attachment import Attachment
from app.models.college_task import CollegeTask
from app.models.complaint import Complaint
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.hour_application import HourApplication
from app.models.hour_application_member import HourApplicationMember
from app.models.operation_log import OperationLog
from app.models.rule_file import RuleFile
from app.models.student import Student
from app.models.task_member import TaskMember
from app.models.task_registration import TaskRegistration
from app.models.task_result_submission import TaskResultSubmission
from app.models.task_result_submission_version import TaskResultSubmissionVersion
from app.models.task_type import TaskType
from app.models.teacher import Teacher
from app.services.week3_hour_application_service import BusinessError, current_student, current_teacher
from app.services.week3_hour_application_service import advisor_approve, advisor_reject, assign_reviewer, reviewer_approve, reviewer_reject
from app.services.week4_credit_exchange_service import advisor_approve_credit_exchange, advisor_reject_credit_exchange
from app.utils.number_generator import generate_application_no
from app.utils.pagination import finish_query
from app.utils.time_utils import business_now, parse_api_datetime


APPEAL_TARGET_TYPES = {"hour_application", "credit_exchange"}
HOUR_APPEALABLE_STATUSES = {"reviewer_modified_approved", "reviewer_rejected", "final_rejected", "material_overdue"}
CREDIT_APPEALABLE_STATUSES = {"final_rejected"}


def create_appeal(user, payload):
    student = current_student(user)
    target_type = _required_choice(payload.get("target_type"), APPEAL_TARGET_TYPES, "申诉对象类型不合法")
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
    query = query.order_by(Appeal.created_at.desc(), Appeal.id.desc())
    return finish_query(query, page, page_size)


def get_student_appeal(user, appeal_id):
    student = current_student(user)
    appeal = Appeal.query.filter_by(id=appeal_id, applicant_student_id=student.id).first()
    if not appeal:
        raise BusinessError("申诉不存在或不可见", code=40401, status=404)
    return appeal


def list_admin_appeals(status=None, page=None, page_size=None):
    query = Appeal.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Appeal.created_at.desc(), Appeal.id.desc())
    return finish_query(query, page, page_size)


def get_admin_appeal(appeal_id):
    appeal = db.session.get(Appeal, appeal_id)
    if not appeal:
        raise BusinessError("申诉不存在", code=40401, status=404)
    return appeal


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
    teacher = current_teacher(user, "advisor")
    hour_ids = db.session.query(ApplicationAdvisor.application_id).filter_by(
            teacher_id=teacher.id,
            advisor_role="primary",
            can_operate=True,
        )
    exchange_ids = db.session.query(CreditExchangeApplication.id).filter_by(advisor_teacher_id=teacher.id)
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
            )
            if decision == "approve"
            else advisor_reject(
                user,
                appeal.target_id,
                comment,
                material=reuse_submitted_material,
            )
        )
        appeal.reopen_stage = "pending_assignment" if decision == "approve" else "advisor_rejected"
    else:
        target = advisor_approve_credit_exchange(user, appeal.target_id, comment) if decision == "approve" else advisor_reject_credit_exchange(user, appeal.target_id, comment)
        appeal.reopen_stage = "pending_admin_final" if decision == "approve" else "advisor_rejected"
    if decision == "reject":
        appeal.status = "completed"
    appeal.reconfirmed_by = user.id
    appeal.reconfirmed_at = business_now()
    _add_operation(user.id, "appeal", appeal.id, f"advisor_reconfirm_{decision}", "pending_advisor_confirmation", appeal.reopen_stage)
    db.session.commit()
    return appeal, target


def list_reopened_pending_assignment(page=None, page_size=None):
    query = Appeal.query.filter_by(status="processing", reopen_stage="pending_assignment").order_by(Appeal.id.desc())
    return finish_query(query, page, page_size)


def assign_reopened_appeal(user, appeal_id, reviewer_teacher_id, comment=None):
    appeal = get_admin_appeal(appeal_id)
    if appeal.target_type != "hour_application" or appeal.reopen_stage != "pending_assignment":
        raise BusinessError("当前申诉不允许分配审核老师", code=40901, status=409)
    target = assign_reviewer(user, appeal.target_id, reviewer_teacher_id, comment)
    appeal.reopen_stage = "pending_reviewer_review"
    _add_operation(user.id, "appeal", appeal.id, "assign_reviewer", "pending_assignment", appeal.reopen_stage)
    db.session.commit()
    return appeal, target


def list_reviewer_appeals(user, page=None, page_size=None):
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


def review_reopened_appeal(user, appeal_id, decision, comment=None, suggested_hours=None):
    appeal = get_reviewer_appeal(user, appeal_id)
    if decision == "approve":
        target, _ = reviewer_approve(user, appeal.target_id, comment)
    elif decision == "modified_approve":
        target, _ = reviewer_approve(user, appeal.target_id, comment, suggested_hours, modified=True)
    elif decision == "reject":
        target = reviewer_reject(user, appeal.target_id, comment)
    else:
        raise BusinessError("复审决定不合法")
    appeal.reopen_stage = "pending_admin_final" if decision != "reject" else "reviewer_rejected"
    if decision == "reject":
        appeal.status = "completed"
    _add_operation(user.id, "appeal", appeal.id, f"reviewer_{decision}", "pending_reviewer_review", appeal.reopen_stage)
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


def create_task(user, payload, publisher_type, submit=True):
    task_type = _get_task_type(_required_int(payload, "task_type_id"))
    if publisher_type == "admin" and not task_type.allow_admin_task:
        raise BusinessError("该任务类别不允许管理员发布任务")
    if publisher_type == "teacher" and not task_type.allow_teacher_task:
        raise BusinessError("该任务类别不允许指导老师发布任务")
    advisor = _task_advisor(user, payload, publisher_type)
    deadline = _parse_datetime(payload.get("registration_deadline"))
    if not deadline or deadline <= business_now():
        raise BusinessError("报名截止时间必须晚于当前时间")
    status = "draft"
    if submit and publisher_type == "admin":
        status = "published"
    elif submit:
        status = "pending_publish_review"
    task = CollegeTask(
        task_no=generate_application_no("TK"),
        title=_required_str(payload, "title"),
        description=_required_str(payload, "description"),
        task_type_id=task_type.id,
        major_name=(payload.get("major_name") or advisor.major_name or "通用专业").strip(),
        course_name=(payload.get("course_name") or advisor.course_name or "通用课程").strip(),
        requirement=_required_str(payload, "result_requirement", "requirement"),
        publisher_type=publisher_type,
        publisher_user_id=user.id,
        advisor_teacher_id=advisor.id,
        registration_start_at=business_now() if status == "published" else None,
        registration_deadline=deadline,
        status=status,
        published_at=business_now() if status == "published" else None,
    )
    db.session.add(task)
    db.session.flush()
    _add_operation(user.id, "college_task", task.id, "submit" if submit else "draft", None, task.status)
    db.session.commit()
    return task


def list_student_tasks(user, keyword=None, task_type_id=None, page=None, page_size=None):
    _advance_expired_task_registrations()
    query = CollegeTask.query.filter(
        CollegeTask.status.in_(["published", "registration_open"]),
        CollegeTask.registration_deadline > business_now(),
    )
    if keyword:
        query = query.filter(or_(CollegeTask.title.like(f"%{keyword}%"), CollegeTask.description.like(f"%{keyword}%")))
    if task_type_id:
        query = query.filter_by(task_type_id=int(task_type_id))
    query = query.order_by(CollegeTask.created_at.desc(), CollegeTask.id.desc())
    return finish_query(query, page, page_size)


def get_student_task(user, task_id):
    task = _get_task(task_id)
    _advance_task_registration(task)
    if task.status not in {"published", "registration_open", "registration_closed", "selection_pending", "leader_pending", "task_in_progress"}:
        raise BusinessError("任务不存在或不可见", code=40401, status=404)
    student = current_student(user)
    registration = TaskRegistration.query.filter_by(task_id=task.id, student_id=student.id).first()
    return task, registration


def register_task(user, task_id, payload):
    student = current_student(user)
    task = _get_task(task_id)
    _advance_task_registration(task)
    if task.status not in {"published", "registration_open"} or task.registration_deadline <= business_now():
        raise BusinessError("当前任务不在报名期", code=40901, status=409)
    exists = TaskRegistration.query.filter_by(task_id=task.id, student_id=student.id).first()
    if exists:
        raise BusinessError("不能重复报名同一任务", code=40902, status=409)
    registration = TaskRegistration(
        task_id=task.id,
        student_id=student.id,
        apply_reason=(payload.get("remark") or payload.get("apply_reason") or "").strip() or None,
        status="submitted",
    )
    db.session.add(registration)
    _add_operation(user.id, "task_registration", task.id, "register", None, "submitted")
    db.session.commit()
    return registration


def list_my_tasks(user, status=None):
    student = current_student(user)
    _advance_expired_task_registrations()
    query = CollegeTask.query.outerjoin(TaskRegistration, TaskRegistration.task_id == CollegeTask.id).outerjoin(
        TaskMember,
        TaskMember.task_id == CollegeTask.id,
    ).filter(or_(TaskRegistration.student_id == student.id, TaskMember.student_id == student.id))
    if status:
        query = query.filter(or_(CollegeTask.status == status, TaskRegistration.status == status))
    return query.order_by(CollegeTask.created_at.desc(), CollegeTask.id.desc()).distinct().all()


def get_student_registration(user, registration_id):
    student = current_student(user)
    registration = TaskRegistration.query.filter_by(id=registration_id, student_id=student.id).first()
    if not registration:
        raise BusinessError("报名记录不存在或不可见", code=40401, status=404)
    return registration


def list_advisor_tasks(user, status=None):
    teacher = current_teacher(user, "advisor")
    _advance_expired_task_registrations()
    query = CollegeTask.query.filter_by(advisor_teacher_id=teacher.id)
    if status:
        query = query.filter_by(status=status)
    return query.order_by(CollegeTask.created_at.desc(), CollegeTask.id.desc()).all()


def get_advisor_task(user, task_id):
    teacher = current_teacher(user, "advisor")
    task = _get_task(task_id)
    _advance_task_registration(task)
    if task.advisor_teacher_id != teacher.id:
        raise BusinessError("当前教师不是该任务指导老师", code=40301, status=403)
    return task


def list_task_registrations_for_advisor(user, task_id):
    task = get_advisor_task(user, task_id)
    return sorted(task.registrations, key=lambda item: (item.created_at, item.id))


def select_task_registrations(user, task_id, payload):
    task = get_advisor_task(user, task_id)
    if task.status != "selection_pending":
        if task.status in {"published", "registration_open"}:
            raise BusinessError("报名尚未截止，暂不能筛选", code=40901, status=409)
        raise BusinessError("当前任务状态不允许筛选报名", code=40901, status=409)
    selected_ids = _normalize_id_list(payload.get("selected_registration_ids"))
    not_selected_ids = _normalize_id_list(payload.get("not_selected_registration_ids"))
    if not selected_ids:
        raise BusinessError("至少选择一名报名学生")
    overlap = set(selected_ids) & set(not_selected_ids)
    if overlap:
        raise BusinessError("选中和未选中报名记录不能重复")
    registrations = TaskRegistration.query.filter(TaskRegistration.task_id == task.id).all()
    by_id = {item.id: item for item in registrations}
    if not set(selected_ids + not_selected_ids).issubset(by_id):
        raise BusinessError("报名记录不存在或不属于当前任务", code=40401, status=404)
    TaskMember.query.filter_by(task_id=task.id).delete()
    now = business_now()
    for registration_id in selected_ids:
        registration = by_id[registration_id]
        registration.status = "selected"
        registration.selected_by = user.id
        registration.selected_at = now
        db.session.add(
            TaskMember(
                task_id=task.id,
                registration_id=registration.id,
                student_id=registration.student_id,
                is_leader=False,
                selected_by=user.id,
                status="active",
            )
        )
    for registration_id in not_selected_ids:
        registration = by_id[registration_id]
        registration.status = "not_selected"
        registration.selected_by = user.id
        registration.selected_at = now
    before = task.status
    task.status = "leader_pending"
    _add_operation(user.id, "college_task", task.id, "select_registrations", before, task.status)
    db.session.commit()
    return task


def selected_task_members(user, task_id):
    task = get_advisor_task(user, task_id)
    return task, [item for item in task.members if item.status == "active"]


def assign_task_leader(user, task_id, leader_student_id):
    task = get_advisor_task(user, task_id)
    if task.status != "leader_pending":
        raise BusinessError("当前任务不在等待指定队长状态", code=40901, status=409)
    members = [item for item in task.members if item.status == "active"]
    try:
        leader_student_id = int(leader_student_id)
    except (TypeError, ValueError):
        raise BusinessError("leader_student_id 必须是整数")
    if leader_student_id not in {item.student_id for item in members}:
        raise BusinessError("队长必须来自最终参与成员")
    for member in members:
        member.is_leader = member.student_id == leader_student_id
    before = task.status
    task.status = "task_in_progress"
    _add_operation(user.id, "college_task", task.id, "assign_leader", before, task.status)
    db.session.commit()
    return task, leader_student_id


def get_student_team(user, task_id):
    student = current_student(user)
    task = _get_task(task_id)
    members = [item for item in task.members if item.status == "active"]
    if student.id not in {item.student_id for item in members}:
        raise BusinessError("只有最终参与成员可以查看团队信息", code=40301, status=403)
    return task, members, student


def submit_task_result(user, task_id, payload):
    student = current_student(user)
    task = _get_task(task_id)
    members = [item for item in task.members if item.status == "active"]
    leader = next((item for item in members if item.is_leader), None)
    if not leader or leader.student_id != student.id:
        raise BusinessError("只有任务队长可以提交成果", code=40301, status=403)
    if TaskResultSubmission.query.filter_by(task_id=task.id).first():
        raise BusinessError("该任务已经提交成果", code=40902, status=409)
    summary = _required_str(payload, "summary")
    attachment_ids = _normalize_id_list(payload.get("attachment_ids"))
    if not attachment_ids:
        raise BusinessError("任务成果必须上传附件")
    try:
        requested_hours = Decimal(str(payload.get("requested_hours")))
    except (InvalidOperation, TypeError, ValueError):
        raise BusinessError("申请课时必须是数字")
    if requested_hours <= 0:
        raise BusinessError("申请课时必须大于 0")

    application = HourApplication(
        application_no=generate_application_no("HT"),
        student_id=student.id,
        applicant_student_id=student.id,
        leader_student_id=student.id,
        application_type="task_result",
        source_type="admin_task" if task.publisher_type == "admin" else "teacher_task",
        source_task_id=task.id,
        task_type_id=task.task_type_id,
        task_type_code=task.task_type.type_code,
        title=task.title,
        major_name=task.major_name,
        course_name=task.course_name,
        requested_hours=requested_hours,
        achievement_summary=summary,
        description=task.description,
        status="submitted",
        submitted_at=business_now(),
    )
    db.session.add(application)
    db.session.flush()
    submission = TaskResultSubmission(
        task_id=task.id,
        leader_student_id=student.id,
        summary=summary,
        requested_hours=requested_hours,
        status="submitted",
        hour_application_id=application.id,
    )
    db.session.add(submission)
    db.session.flush()
    db.session.add(TaskResultSubmissionVersion(
        submission_id=submission.id,
        version_no=1,
        summary=summary,
        requested_hours=requested_hours,
        attachment_ids=attachment_ids,
        submitted_by=user.id,
    ))
    application.task_result_submission_id = submission.id
    for member in members:
        db.session.add(HourApplicationMember(
            application_id=application.id,
            student_id=member.student_id,
            is_leader=member.is_leader,
            can_view=True,
            can_apply_credit_exchange=member.is_leader,
        ))
    db.session.add(ApplicationAdvisor(
        application_id=application.id,
        teacher_id=task.advisor_teacher_id,
        advisor_role="primary",
        can_operate=True,
    ))
    _bind_attachments("task_result", submission.id, attachment_ids, user.id)
    task.status = "result_submitted"
    _add_operation(user.id, "task_result", submission.id, "submit", None, submission.status)
    db.session.commit()
    return submission


def resubmit_task_result(user, submission_id, payload):
    student = current_student(user)
    submission = db.session.get(TaskResultSubmission, submission_id)
    if not submission:
        raise BusinessError("任务成果不存在", code=40401, status=404)
    task = submission.task
    if submission.leader_student_id != student.id:
        raise BusinessError("只有任务队长可以重新提交成果", code=40301, status=403)
    _require_status(submission.status, "advisor_rejected")
    if task.status != "task_in_progress":
        raise BusinessError("当前任务状态不允许重新提交成果", code=40901, status=409)

    summary = _required_str(payload, "summary")
    attachment_ids = _normalize_id_list(payload.get("attachment_ids"))
    if not attachment_ids:
        raise BusinessError("重新提交成果必须上传附件")
    try:
        requested_hours = Decimal(str(payload.get("requested_hours")))
    except (InvalidOperation, TypeError, ValueError):
        raise BusinessError("申请课时必须是数字")
    if requested_hours <= 0:
        raise BusinessError("申请课时必须大于 0")

    application = submission.hour_application
    if not application or application.status != "advisor_rejected":
        raise BusinessError("关联课时申请状态不允许重新提交成果", code=40901, status=409)

    _bind_attachments("task_result", submission.id, attachment_ids, user.id)
    latest_version = max((item.version_no for item in submission.versions), default=0)
    db.session.add(TaskResultSubmissionVersion(
        submission_id=submission.id,
        version_no=latest_version + 1,
        summary=summary,
        requested_hours=requested_hours,
        attachment_ids=attachment_ids,
        submitted_by=user.id,
    ))

    before = submission.status
    submission.summary = summary
    submission.requested_hours = requested_hours
    submission.status = "submitted"
    submission.advisor_comment = None
    submission.advisor_reviewed_by = None
    submission.advisor_reviewed_at = None
    application.achievement_summary = summary
    application.requested_hours = requested_hours
    application.status = "submitted"
    application.advisor_reviewed_at = None
    primary_advisor = ApplicationAdvisor.query.filter_by(
        application_id=application.id,
        advisor_role="primary",
        can_operate=True,
    ).first()
    if primary_advisor:
        primary_advisor.reviewed_at = None
    task.status = "result_submitted"
    _add_operation(user.id, "task_result", submission.id, "resubmit", before, submission.status)
    db.session.commit()
    return submission


def get_advisor_task_result(user, submission_id):
    teacher = current_teacher(user, "advisor")
    submission = db.session.get(TaskResultSubmission, submission_id)
    if not submission or submission.task.advisor_teacher_id != teacher.id:
        raise BusinessError("任务成果不存在或无权查看", code=40401, status=404)
    return submission


def list_advisor_task_results(user, status="submitted", page=None, page_size=None):
    teacher = current_teacher(user, "advisor")
    query = TaskResultSubmission.query.join(
        CollegeTask,
        TaskResultSubmission.task_id == CollegeTask.id,
    ).filter(CollegeTask.advisor_teacher_id == teacher.id)
    if status:
        query = query.filter(TaskResultSubmission.status == status)
    query = query.order_by(TaskResultSubmission.created_at.desc(), TaskResultSubmission.id.desc())
    return finish_query(query, page, page_size)


def review_task_result(user, submission_id, approve, comment=None):
    submission = get_advisor_task_result(user, submission_id)
    _require_status(submission.status, "submitted")
    if not approve and not (comment or "").strip():
        raise BusinessError("驳回原因不能为空")
    application = submission.hour_application
    if approve:
        advisor_approve(user, application.id, comment)
    else:
        advisor_reject(user, application.id, comment)
    return submission


def create_complaint(user, payload):
    current_student(user)
    complaint = Complaint(submitter_user_id=user.id, content=_required_str(payload, "content"), status="submitted")
    db.session.add(complaint)
    db.session.flush()
    _bind_attachments("complaint", complaint.id, payload.get("attachment_ids"), user.id)
    _add_operation(user.id, "complaint", complaint.id, "submit", None, complaint.status)
    db.session.commit()
    return complaint


def list_complaints(status=None, page=None, page_size=None):
    query = Complaint.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(Complaint.id.desc())
    return finish_query(query, page, page_size)


def get_complaint(complaint_id, mark_viewed=False):
    complaint = db.session.get(Complaint, complaint_id)
    if not complaint:
        raise BusinessError("投诉不存在", code=40401, status=404)
    if mark_viewed and complaint.status == "submitted":
        complaint.status = "viewed"
        complaint.viewed_at = business_now()
        db.session.commit()
    return complaint


def list_admin_tasks(status=None, page=None, page_size=None):
    _advance_expired_task_registrations()
    query = CollegeTask.query
    if status:
        query = query.filter_by(status=status)
    query = query.order_by(CollegeTask.created_at.desc(), CollegeTask.id.desc())
    return finish_query(query, page, page_size)


def get_admin_task(task_id):
    task = _get_task(task_id)
    _advance_task_registration(task)
    return task


def list_pending_task_publish_requests(page=None, page_size=None):
    query = CollegeTask.query.filter_by(status="pending_publish_review").order_by(CollegeTask.created_at.desc())
    return finish_query(query, page, page_size)


def admin_approve_task_publish(user, task_id, comment=None):
    task = _get_task(task_id)
    _require_status(task.status, "pending_publish_review")
    before = task.status
    task.status = "published"
    task.admin_reviewed_by = user.id
    task.admin_review_comment = (comment or "").strip() or None
    task.registration_start_at = task.registration_start_at or business_now()
    task.published_at = business_now()
    _add_operation(user.id, "college_task", task.id, "publish_approved", before, task.status)
    db.session.commit()
    return task


def admin_reject_task_publish(user, task_id, comment):
    if not comment:
        raise BusinessError("驳回原因不能为空")
    task = _get_task(task_id)
    _require_status(task.status, "pending_publish_review")
    before = task.status
    task.status = "publish_rejected"
    task.admin_reviewed_by = user.id
    task.admin_review_comment = comment
    _add_operation(user.id, "college_task", task.id, "publish_rejected", before, task.status)
    db.session.commit()
    return task


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


def _task_advisor(user, payload, publisher_type):
    if publisher_type == "teacher":
        return current_teacher(user, "advisor")
    teacher_id = _required_int(payload, "advisor_teacher_id")
    teacher = Teacher.query.filter_by(id=teacher_id, status="active").first()
    if not teacher or "advisor" not in teacher.role_flag_list:
        raise BusinessError("指导老师不存在或没有指导老师权限", code=40401, status=404)
    return teacher


def _get_task_type(task_type_id):
    item = TaskType.query.filter_by(id=task_type_id, status="enabled").first()
    if not item:
        raise BusinessError("任务类别不存在或已停用", code=40401, status=404)
    return item


def _get_task(task_id):
    task = db.session.get(CollegeTask, task_id)
    if not task:
        raise BusinessError("任务不存在", code=40401, status=404)
    return task


def _advance_expired_task_registrations():
    changed = CollegeTask.query.filter(
        CollegeTask.status.in_(["published", "registration_open"]),
        CollegeTask.registration_deadline <= business_now(),
    ).update({"status": "selection_pending"}, synchronize_session="fetch")
    if changed:
        db.session.commit()


def _advance_task_registration(task):
    if (
        task.status in {"published", "registration_open"}
        and task.registration_deadline
        and task.registration_deadline <= business_now()
    ):
        task.status = "selection_pending"
        db.session.commit()


def _bind_attachments(owner_type, owner_id, attachment_ids, user_id):
    ids = _normalize_id_list(attachment_ids)
    if not ids:
        return
    attachments = Attachment.query.filter(Attachment.id.in_(ids), Attachment.status == "active").all()
    if len(attachments) != len(set(ids)):
        raise BusinessError("附件不存在或无权使用", code=40301, status=403)
    for attachment in attachments:
        if attachment.uploaded_by != user_id or attachment.biz_type != owner_type:
            raise BusinessError("附件不存在或无权使用", code=40301, status=403)
        if attachment.owner_id and attachment.owner_id != owner_id:
            raise BusinessError("附件已绑定其他业务", code=40902, status=409)
        attachment.owner_type = owner_type
        attachment.owner_id = owner_id


def _add_operation(user_id, biz_type, biz_id, action, before_status, after_status):
    db.session.add(
        OperationLog(
            user_id=user_id,
            module="week5",
            biz_type=biz_type,
            biz_id=biz_id,
            action=action,
            detail=f"{before_status}->{after_status}",
        )
    )


def _require_status(actual, expected):
    if actual != expected:
        raise BusinessError("当前状态不允许执行该操作", code=40901, status=409)


def _required_str(payload, *keys):
    for key in keys:
        value = (payload.get(key) or "").strip()
        if value:
            return value
    raise BusinessError(f"{keys[0]} 不能为空")


def _required_int(payload, key):
    value = payload.get(key)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise BusinessError(f"{key} 必须是整数")
    if value <= 0:
        raise BusinessError(f"{key} 必须大于 0")
    return value


def _required_choice(value, choices, message):
    value = (value or "").strip()
    if value not in choices:
        raise BusinessError(message)
    return value


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
