from decimal import Decimal, InvalidOperation

from sqlalchemy import or_

from app.core.errors import BusinessError
from app.core.validators import is_mainland_mobile
from app.core.identity import current_student, current_teacher
from app.extensions import db
from app.models.application_advisor import ApplicationAdvisor
from app.models.college_task import CollegeTask
from app.models.hour_application import HourApplication
from app.models.hour_application_member import HourApplicationMember
from app.models.task_member import TaskMember
from app.models.task_registration import TaskRegistration
from app.models.task_result_submission import TaskResultSubmission
from app.models.task_result_submission_version import TaskResultSubmissionVersion
from app.models.task_type import TaskType
from app.models.teacher import Teacher
from app.services.service_helpers import (
    add_operation as _add_operation,
    bind_attachments as _bind_attachments,
    normalize_id_list as _normalize_id_list,
    parse_datetime as _parse_datetime,
    required_int as _required_int,
    required_str as _required_str,
    require_status as _require_status,
)
from app.services.notification_service import create_notification
from app.services.week3_hour_application_service import advisor_approve, advisor_reject
from app.utils.number_generator import generate_application_no
from app.utils.pagination import finish_query
from app.utils.time_utils import business_now


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
    _bind_attachments(
        "college_task",
        task.id,
        payload.get("attachment_ids"),
        user.id,
        expected_biz_type="task",
    )
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
    if not isinstance(payload, dict):
        raise BusinessError("请求体必须是 JSON 对象")
    allowed_fields = {"contact_phone", "remark", "apply_reason"}
    if set(payload) - allowed_fields:
        raise BusinessError("请求包含未定义字段")
    if "remark" in payload and "apply_reason" in payload:
        raise BusinessError("remark 和 apply_reason 不能同时提交")
    raw_phone = payload.get("contact_phone")
    if not isinstance(raw_phone, str) or not is_mainland_mobile(raw_phone):
        raise BusinessError("contact_phone 必须是有效的11位中国大陆手机号")
    contact_phone = raw_phone.strip()
    remark = payload.get("remark", payload.get("apply_reason"))
    if remark is not None and not isinstance(remark, str):
        raise BusinessError("remark 必须是字符串或 null")
    remark = (remark or "").strip() or None
    if remark and len(remark) > 1000:
        raise BusinessError("remark 最多 1000 个字符")
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
        apply_reason=remark,
        contact_phone=contact_phone,
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
    handled_ids = set(selected_ids + not_selected_ids)
    if not handled_ids.issubset(by_id):
        raise BusinessError("报名记录不存在或不属于当前任务", code=40401, status=404)
    unhandled_ids = set(by_id) - handled_ids
    if unhandled_ids:
        raise BusinessError(
            "必须处理当前任务的全部报名学生",
            code=40901,
            status=409,
        )
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
        create_notification(
            registration.student.user_id, user.id, "task", "task_registration_selected",
            "任务报名已入选", f"您报名的任务“{task.title}”已入选。",
            biz_type="college_task", biz_id=task.id,
            payload={"registration_id": registration.id, "status": registration.status},
            dedupe_key=f"task-registration:{registration.id}:1:selected",
        )
    for registration_id in not_selected_ids:
        registration = by_id[registration_id]
        registration.status = "not_selected"
        registration.selected_by = user.id
        registration.selected_at = now
        create_notification(
            registration.student.user_id, user.id, "task", "task_registration_not_selected",
            "任务报名未入选", f"您报名的任务“{task.title}”本轮未入选。",
            biz_type="college_task", biz_id=task.id,
            payload={"registration_id": registration.id, "status": registration.status},
            dedupe_key=f"task-registration:{registration.id}:1:not-selected",
        )
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
    notification = create_notification(
        task.advisor.user_id, user.id, "hour_application", "hour_application_submitted",
        "新的任务成果待确认",
        f"学生已提交任务“{task.title}”的成果及课时申请，请及时确认。",
        biz_type="hour_application", biz_id=application.id,
        payload={
            "application_no": application.application_no,
            "task_id": task.id,
            "task_result_submission_id": submission.id,
            "status": application.status,
        },
        dedupe_key=f"hour-application:{application.id}:submitted:initial",
    )
    if notification is None:
        raise BusinessError("任务指导老师账号不可用，不能提交成果", code=40902, status=409)
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
    notification = create_notification(
        task.advisor.user_id, user.id, "hour_application", "hour_application_material_submitted",
        "补交任务成果待确认",
        f"学生已重新提交任务“{task.title}”的成果及课时申请，请及时确认。",
        biz_type="hour_application", biz_id=application.id,
        payload={
            "application_no": application.application_no,
            "task_id": task.id,
            "task_result_submission_id": submission.id,
            "status": application.status,
        },
        dedupe_key=f"hour-application:{application.id}:task-result:submitted:{latest_version + 1}",
    )
    if notification is None:
        raise BusinessError("任务指导老师账号不可用，不能重新提交成果", code=40902, status=409)
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
    create_notification(
        task.publisher_user_id, user.id, "task", "task_publish_approved",
        "任务发布申请已通过", f"您提交的任务“{task.title}”已通过管理员审核并发布。",
        biz_type="college_task", biz_id=task.id,
        payload={"task_no": task.task_no, "status": task.status},
        dedupe_key=f"task-publish:{task.id}:1:approved",
    )
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
    create_notification(
        task.publisher_user_id, user.id, "task", "task_publish_rejected",
        "任务发布申请已驳回", f"您提交的任务“{task.title}”未通过管理员审核。原因：{comment}",
        biz_type="college_task", biz_id=task.id,
        payload={"task_no": task.task_no, "status": task.status},
        dedupe_key=f"task-publish:{task.id}:1:rejected",
    )
    db.session.commit()
    return task


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
