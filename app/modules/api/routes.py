from io import BytesIO

import os
import uuid
from decimal import Decimal

from flask import Blueprint, Response, current_app, jsonify, request, send_file
from flask_login import current_user, login_required, login_user, logout_user
from openpyxl import Workbook
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.attachment import Attachment
from app.models.student import Student
from app.models.task_type import TaskType
from app.models.teacher import Teacher
from app.services.auth_service import authenticate_user
from app.services.import_service import import_admins, import_students, import_teachers
from app.services.task_type_service import (
    create_task_type,
    list_task_types,
    set_task_type_status,
    task_type_to_dict,
    update_task_type,
)
from app.services.week3_hour_application_service import (
    BusinessError,
    advisor_approve,
    advisor_reject,
    assign_reviewer,
    create_student_application,
    current_teacher,
    final_approve,
    final_reject,
    get_advisor_application,
    get_application,
    get_reviewer_application,
    get_visible_application_for_student,
    latest_reviewer_result,
    list_admin_hour_applications,
    list_advisor_material_pending,
    list_advisor_pending,
    list_pending_assignment,
    list_pending_final,
    list_reviewer_pending,
    list_student_hour_applications,
    reviewer_approve,
    reviewer_reject,
    submit_materials,
)
from app.utils.permissions import role_required


api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    remember = bool(data.get("remember"))
    if not username or not password:
        return fail("账号和密码不能为空")

    user = authenticate_user(username, password)
    if not user:
        return fail("账号或密码错误，或账号已被禁用", code=40101, status=401)

    login_user(user, remember=remember)
    user.last_login_at = db.func.now()
    db.session.commit()
    return ok(_current_user_payload())


@api_bp.route("/auth/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return ok()


@api_bp.route("/me")
@login_required
def me():
    return ok(_current_user_payload())


def _current_user_payload():
    student = Student.query.filter_by(user_id=current_user.id).first()
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.effective_role,
        "roles": current_user.roles,
        "student": _student_summary(student) if student else None,
        "teacher": _teacher_summary(teacher) if teacher else None,
    }


@api_bp.route("/task-types")
@login_required
def get_task_types():
    enabled = _parse_bool_query(request.args.get("enabled"))
    return ok({"items": [task_type_to_dict(item) for item in list_task_types(enabled=enabled)]})


@api_bp.route("/teachers/advisors")
@login_required
def get_advisors():
    return ok({"items": [_teacher_summary(item) for item in _list_teachers_by_flag("advisor")]})


@api_bp.route("/admin/reviewers")
@login_required
@role_required("admin")
def admin_get_reviewers():
    return ok({"items": [_teacher_summary(item) for item in _list_teachers_by_flag("reviewer")]})


@api_bp.route("/admin/task-types", methods=["GET"])
@login_required
@role_required("admin")
def admin_get_task_types():
    enabled = _parse_bool_query(request.args.get("enabled"))
    return ok({"items": [task_type_to_dict(item) for item in list_task_types(enabled=enabled)]})


@api_bp.route("/admin/task-types", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_task_type():
    data = request.get_json(silent=True) or {}
    error = _validate_task_type_payload(data, creating=True)
    if error:
        return fail(error)
    try:
        item = create_task_type(data)
    except IntegrityError:
        db.session.rollback()
        return fail("任务类别编码已存在", code=40902, status=409)
    return ok(task_type_to_dict(item))


@api_bp.route("/admin/task-types/<int:task_type_id>", methods=["PUT", "PATCH"])
@login_required
@role_required("admin")
def admin_update_task_type(task_type_id):
    item = TaskType.query.get_or_404(task_type_id)
    data = request.get_json(silent=True) or {}
    error = _validate_task_type_payload(data, creating=False)
    if error:
        return fail(error)
    try:
        item = update_task_type(item, data)
    except IntegrityError:
        db.session.rollback()
        return fail("任务类别编码已存在", code=40902, status=409)
    return ok(task_type_to_dict(item))


@api_bp.route("/admin/task-types/<int:task_type_id>/enable", methods=["POST"])
@login_required
@role_required("admin")
def admin_enable_task_type(task_type_id):
    item = TaskType.query.get_or_404(task_type_id)
    return ok(task_type_to_dict(set_task_type_status(item, "enabled")))


@api_bp.route("/admin/task-types/<int:task_type_id>/disable", methods=["POST"])
@login_required
@role_required("admin")
def admin_disable_task_type(task_type_id):
    item = TaskType.query.get_or_404(task_type_id)
    return ok(task_type_to_dict(set_task_type_status(item, "disabled")))


@api_bp.route("/admin/import-templates/<target>")
@login_required
@role_required("admin")
def admin_import_template(target):
    templates = {
        "students": ["student_no", "name", "username", "password", "phone", "email", "college", "major", "grade", "class_name", "status"],
        "teachers": ["teacher_no", "name", "username", "password", "phone", "email", "major_name", "course_name", "role_flags", "status"],
        "admins": ["username", "name", "password", "phone", "email", "status"],
    }
    headers = templates.get(target)
    if not headers:
        return fail("未知导入模板", code=40401, status=404)
    output = _build_excel_template(headers)
    return Response(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={target}_template.xlsx"},
    )


@api_bp.route("/admin/imports/students", methods=["POST"])
@login_required
@role_required("admin")
def admin_import_students():
    file_storage = _uploaded_file()
    if not file_storage:
        return fail("请上传 Excel 或 CSV 文件")
    return _handle_import(lambda: import_students(file_storage, _import_mode(), current_user.id, request.remote_addr))


@api_bp.route("/admin/imports/teachers", methods=["POST"])
@login_required
@role_required("admin")
def admin_import_teachers():
    file_storage = _uploaded_file()
    if not file_storage:
        return fail("请上传 Excel 或 CSV 文件")
    return _handle_import(lambda: import_teachers(file_storage, _import_mode(), current_user.id, request.remote_addr))


@api_bp.route("/admin/imports/admins", methods=["POST"])
@login_required
@role_required("admin")
def admin_import_admins():
    file_storage = _uploaded_file()
    if not file_storage:
        return fail("请上传 Excel 或 CSV 文件")
    return _handle_import(lambda: import_admins(file_storage, _import_mode(), current_user.id, request.remote_addr))


@api_bp.route("/attachments", methods=["POST"])
@login_required
def upload_attachment():
    file_storage = request.files.get("file")
    biz_type = (request.form.get("biz_type") or "").strip()
    if not file_storage or not file_storage.filename:
        return fail("请上传文件")
    if biz_type not in {"hour_application", "task_result", "credit_exchange", "appeal", "complaint", "rule_file"}:
        return fail("附件业务类型不合法")
    upload_root = current_app.config["UPLOAD_FOLDER"]
    attachment_dir = os.path.join(upload_root, "attachments", biz_type)
    os.makedirs(attachment_dir, exist_ok=True)
    extension = os.path.splitext(file_storage.filename)[1]
    stored_name = f"{uuid.uuid4().hex}{extension}"
    stored_path = os.path.join(attachment_dir, stored_name)
    file_storage.save(stored_path)
    relative_path = os.path.relpath(stored_path, current_app.root_path).replace("\\", "/")
    size = os.path.getsize(stored_path)
    attachment = Attachment(
        biz_type=biz_type,
        file_name=file_storage.filename,
        file_path=relative_path,
        file_size=size,
        mime_type=file_storage.mimetype,
        uploaded_by=current_user.id,
    )
    db.session.add(attachment)
    db.session.commit()
    return ok(_attachment_summary(attachment))


@api_bp.route("/attachments/<int:attachment_id>", methods=["GET"])
@login_required
def get_attachment(attachment_id):
    attachment = Attachment.query.filter_by(id=attachment_id, status="active").first()
    if not attachment:
        return fail("附件不存在", code=40401, status=404)
    if attachment.uploaded_by != current_user.id and "admin" not in current_user.roles:
        return fail("无权访问该附件", code=40301, status=403)
    if _parse_bool_query(request.args.get("download")):
        path = os.path.join(current_app.root_path, attachment.file_path)
        return send_file(path, as_attachment=True, download_name=attachment.file_name)
    return ok(_attachment_summary(attachment))


@api_bp.route("/student/hour-applications", methods=["POST"])
@login_required
@role_required("student")
def student_submit_hour_application():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_application_created_payload(create_student_application(current_user, data, submit=True))))


@api_bp.route("/student/hour-applications", methods=["GET"])
@login_required
@role_required("student")
def student_hour_applications():
    status = (request.args.get("status") or "").strip() or None
    role = (request.args.get("role") or "").strip() or None
    return _handle_business(lambda: ok({"items": [_hour_application_summary(item) for item in list_student_hour_applications(current_user, status, role)]}))


@api_bp.route("/student/hour-applications/<int:application_id>", methods=["GET"])
@login_required
@role_required("student")
def student_hour_application_detail(application_id):
    return _handle_business(lambda: ok(_hour_application_detail_payload(get_visible_application_for_student(current_user, application_id))))


@api_bp.route("/student/hour-applications/<int:application_id>/materials", methods=["POST"])
@login_required
@role_required("student")
def student_submit_hour_application_materials(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(submit_materials(current_user, application_id, data))))


@api_bp.route("/advisor/hour-applications/pending", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_pending_hour_applications():
    status = (request.args.get("status") or "submitted").strip()
    return _handle_business(lambda: ok({"items": [_hour_application_summary(item) for item in list_advisor_pending(current_user, status)]}))


@api_bp.route("/advisor/hour-applications/materials/pending", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_pending_materials():
    return _handle_business(lambda: ok({"items": [_hour_application_summary(item) for item in list_advisor_material_pending(current_user)]}))


@api_bp.route("/advisor/hour-applications/<int:application_id>", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_hour_application_detail(application_id):
    return _handle_business(lambda: ok(_advisor_detail_payload(get_advisor_application(current_user, application_id))))


@api_bp.route("/advisor/hour-applications/<int:application_id>/approve", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_approve_hour_application(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(advisor_approve(current_user, application_id, data.get("comment")))))


@api_bp.route("/advisor/hour-applications/<int:application_id>/reject", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_reject_hour_application(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(advisor_reject(current_user, application_id, data.get("comment")))))


@api_bp.route("/advisor/hour-applications/<int:application_id>/materials", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_material_detail(application_id):
    return _handle_business(lambda: ok(_advisor_detail_payload(get_advisor_application(current_user, application_id))))


@api_bp.route("/advisor/hour-applications/<int:application_id>/materials/approve", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_approve_material(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(advisor_approve(current_user, application_id, data.get("comment"), material=True))))


@api_bp.route("/advisor/hour-applications/<int:application_id>/materials/reject", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_reject_material(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(advisor_reject(current_user, application_id, data.get("comment"), material=True))))


@api_bp.route("/admin/hour-applications", methods=["GET"])
@login_required
@role_required("admin")
def admin_hour_applications():
    status = (request.args.get("status") or "").strip() or None
    application_type = (request.args.get("application_type") or "").strip() or None
    keyword = (request.args.get("keyword") or "").strip() or None
    return _handle_business(lambda: ok({"items": [_admin_hour_application_summary(item) for item in list_admin_hour_applications(status, application_type, keyword)]}))


@api_bp.route("/admin/hour-applications/pending-assignment", methods=["GET"])
@login_required
@role_required("admin")
def admin_pending_assignment():
    return _handle_business(lambda: ok({"items": [_hour_application_summary(item) for item in list_pending_assignment()]}))


@api_bp.route("/admin/hour-applications/pending-final", methods=["GET"])
@login_required
@role_required("admin")
def admin_pending_final():
    return _handle_business(lambda: ok({"items": [_pending_final_summary(item) for item in list_pending_final()]}))


@api_bp.route("/admin/hour-applications/<int:application_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_hour_application_detail(application_id):
    return _handle_business(lambda: ok(_admin_detail_payload(get_application(application_id))))


@api_bp.route("/admin/hour-applications/<int:application_id>/assign-reviewer", methods=["POST"])
@login_required
@role_required("admin")
def admin_assign_reviewer(application_id):
    data = request.get_json(silent=True) or {}
    reviewer_teacher_id = data.get("reviewer_teacher_id")
    return _handle_business(lambda: ok(_assign_payload(assign_reviewer(current_user, application_id, reviewer_teacher_id, data.get("comment")))))


@api_bp.route("/reviewer/hour-applications/pending", methods=["GET"])
@login_required
@role_required("reviewer")
def reviewer_pending_hour_applications():
    return _handle_business(lambda: ok({"items": [_hour_application_summary(item) for item in list_reviewer_pending(current_user)]}))


@api_bp.route("/reviewer/hour-applications/<int:application_id>", methods=["GET"])
@login_required
@role_required("reviewer")
def reviewer_hour_application_detail(application_id):
    return _handle_business(lambda: ok(_reviewer_detail_payload(get_reviewer_application(current_user, application_id))))


@api_bp.route("/reviewer/hour-applications/<int:application_id>/approve", methods=["POST"])
@login_required
@role_required("reviewer")
def reviewer_approve_hour_application(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_reviewer_action_payload(*reviewer_approve(current_user, application_id, data.get("comment")))))


@api_bp.route("/reviewer/hour-applications/<int:application_id>/modified-approve", methods=["POST"])
@login_required
@role_required("reviewer")
def reviewer_modified_approve_hour_application(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_reviewer_action_payload(*reviewer_approve(current_user, application_id, data.get("comment"), data.get("reviewer_suggested_hours"), modified=True))))


@api_bp.route("/reviewer/hour-applications/<int:application_id>/reject", methods=["POST"])
@login_required
@role_required("reviewer")
def reviewer_reject_hour_application(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(reviewer_reject(current_user, application_id, data.get("comment")))))


@api_bp.route("/admin/hour-applications/<int:application_id>/final-review", methods=["GET"])
@login_required
@role_required("admin")
def admin_final_review_detail(application_id):
    return _handle_business(lambda: ok(_final_review_payload(get_application(application_id))))


@api_bp.route("/admin/hour-applications/<int:application_id>/final-approve", methods=["POST"])
@login_required
@role_required("admin")
def admin_final_approve(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_final_approve_payload(*final_approve(current_user, application_id, data.get("final_hours"), data.get("comment")))))


@api_bp.route("/admin/hour-applications/<int:application_id>/final-reject", methods=["POST"])
@login_required
@role_required("admin")
def admin_final_reject(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(final_reject(current_user, application_id, data.get("comment")))))


def ok(data=None):
    return jsonify({"code": 0, "message": "success", "data": data or {}})


def fail(message, code=40001, status=400):
    return jsonify({"code": code, "message": message, "data": None}), status


def _handle_business(func):
    try:
        return func()
    except BusinessError as exc:
        return fail(str(exc), code=exc.code, status=exc.status)
    except ValueError as exc:
        return fail(str(exc))


def _application_created_payload(application):
    return {
        "id": application.id,
        "application_no": application.application_no,
        "status": application.status,
    }


def _id_status_payload(application):
    return {"id": application.id, "status": application.status}


def _assign_payload(application):
    return {
        "id": application.id,
        "status": application.status,
        "reviewer_teacher_id": application.assigned_teacher_id,
    }


def _reviewer_action_payload(application, review_result):
    return {"id": application.id, "status": application.status, "review_result": review_result}


def _final_approve_payload(application, award):
    return {"id": application.id, "status": application.status, "hour_award_record_id": award.id}


def _hour_application_summary(application):
    applicant = application.applicant or application.student
    return {
        "id": application.id,
        "application_no": application.application_no,
        "title": application.title,
        "application_type": application.application_type,
        "source_type": application.source_type,
        "task_type_id": application.task_type_id,
        "task_type_name": application.task_type_name,
        "applicant": _student_summary(applicant) if applicant else None,
        "applicant_name": applicant.name if applicant else None,
        "leader": _student_summary(application.leader) if application.leader else None,
        "requested_hours": _number(application.requested_hours),
        "reviewer_suggested_hours": _number(application.reviewer_suggested_hours),
        "final_hours": _number(application.final_hours),
        "status": application.status,
        "submitted_at": _iso(application.submitted_at),
        "created_at": _iso(application.created_at),
        "updated_at": _iso(application.updated_at),
    }


def _admin_hour_application_summary(application):
    item = _hour_application_summary(application)
    item["can_operate"] = application.status in {"pending_assignment", "pending_admin_final"}
    return item


def _pending_final_summary(application):
    item = _hour_application_summary(application)
    result = latest_reviewer_result(application.id)
    item["review_result"] = _review_record(result)["decision"] if result else None
    return item


def _hour_application_detail_payload(application):
    return {
        "id": application.id,
        "application_no": application.application_no,
        "status": application.status,
        "application": _hour_application_detail(application),
        "applicant": _student_summary(application.applicant or application.student),
        "members": _application_members(application),
        "advisors": _application_advisors(application),
        "attachments": _application_attachments(application),
        "reviews": _application_reviews(application),
        "actions": _action_flags(application),
    }


def _advisor_detail_payload(application):
    payload = _hour_application_detail_payload(application)
    payload["can_operate"] = application.status in {"submitted", "material_submitted"}
    return payload


def _admin_detail_payload(application):
    payload = _hour_application_detail_payload(application)
    payload["assignments"] = _review_assignments(application)
    return payload


def _reviewer_detail_payload(application):
    payload = _hour_application_detail_payload(application)
    payload["requested_hours"] = _number(application.requested_hours)
    payload["can_review"] = application.status == "pending_review"
    return payload


def _final_review_payload(application):
    payload = _hour_application_detail_payload(application)
    result = latest_reviewer_result(application.id)
    payload["reviewer_result"] = _review_record(result) if result else None
    payload["final_hours"] = _number(application.final_hours or application.reviewer_suggested_hours)
    return payload


def _hour_application_detail(application):
    item = _hour_application_summary(application)
    item.update(
        {
            "description": application.description,
            "achievement_summary": application.achievement_summary or application.achievement_submission,
            "major_name": application.major_name,
            "course_name": application.course_name,
            "material_due_at": _iso(application.material_due_at),
            "extension_count": application.extension_count,
            "source_task_id": application.source_task_id,
            "task_result_submission_id": application.task_result_submission_id,
            "assigned_reviewer": _teacher_summary(application.assigned_teacher) if application.assigned_teacher else None,
            "appeal_advice": application.appeal_advice,
            "members": _application_members(application),
            "advisors": _application_advisors(application),
            "attachments": _application_attachments(application),
            "reviews": _application_reviews(application),
            "assignments": _review_assignments(application),
            "actions": _action_flags(application),
        }
    )
    return item


def _application_members(application):
    links = sorted(application.member_links, key=lambda item: (not item.is_leader, item.id))
    return [
        {
            "student": _student_summary(link.student),
            "is_leader": bool(link.is_leader),
            "can_view": bool(link.can_view),
            "joined_at": _iso(link.joined_at),
        }
        for link in links
        if link.status == "active"
    ]


def _application_advisors(application):
    links = sorted(application.advisor_links, key=lambda item: (item.advisor_role != "primary", item.id))
    return [
        {
            "teacher": _teacher_summary(link.teacher),
            "advisor_role": link.advisor_role,
            "can_operate": bool(link.can_operate),
            "reviewed_at": _iso(link.reviewed_at),
        }
        for link in links
    ]


def _application_attachments(application):
    generic_items = Attachment.query.filter_by(
        owner_type="hour_application",
        owner_id=application.id,
        status="active",
    ).order_by(Attachment.id.asc()).all()
    summaries = [_attachment_summary(item) for item in generic_items]
    legacy_summaries = [
        {
            "id": item.id,
            "biz_type": "hour_application",
            "file_name": item.file_name,
            "file_size": item.file_size,
            "mime_type": item.file_type,
            "url": f"/static/{item.static_relative_path}",
            "uploaded_by": item.uploaded_by,
            "created_at": _iso(item.created_at),
        }
        for item in getattr(application, "attachments", [])
    ]
    return summaries + legacy_summaries


def _attachment_summary(attachment):
    return {
        "id": attachment.id,
        "biz_type": attachment.biz_type,
        "file_name": attachment.file_name,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
        "url": f"/api/v1/attachments/{attachment.id}",
        "uploaded_by": attachment.uploaded_by,
        "created_at": _iso(attachment.created_at),
    }


def _application_reviews(application):
    reviews = sorted(getattr(application, "reviews", []), key=lambda item: (item.created_at, item.id))
    return [_review_record(item) for item in reviews]


def _review_record(review):
    if not review:
        return None
    return {
        "id": review.id,
        "stage": review.stage or "reviewer",
        "operator_role": review.operator_role or review.stage or "reviewer",
        "operator_name": None,
        "decision": review.decision or review.action,
        "before_status": review.before_status,
        "after_status": review.after_status,
        "requested_hours_snapshot": _number(review.requested_hours_snapshot),
        "approved_hours": _number(review.approved_hours),
        "comment": review.comment,
        "created_at": _iso(review.created_at),
    }


def _review_assignments(application):
    assignments = sorted(getattr(application, "review_assignments", []), key=lambda item: (item.assigned_at, item.id))
    return [
        {
            "id": item.id,
            "reviewer": _teacher_summary(item.reviewer),
            "assigned_by_name": None,
            "assign_type": "assign" if item.status == "active" else "reassign",
            "reason": item.assign_reason,
            "created_at": _iso(item.assigned_at),
        }
        for item in assignments
    ]


def _action_flags(application):
    return {
        "can_edit": application.status in {"draft", "advisor_rejected", "reviewer_rejected"},
        "can_submit": application.status in {"draft", "advisor_rejected", "reviewer_rejected"},
        "can_approve": application.status in {"submitted", "material_submitted", "pending_review", "pending_admin_final"},
        "can_reject": application.status in {"submitted", "material_submitted", "pending_review", "pending_admin_final"},
        "can_assign": application.status == "pending_assignment",
        "can_appeal": application.status in {"reviewer_modified_approved", "reviewer_rejected", "final_rejected"},
        "can_download": True,
    }


def _number(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _iso(value):
    return value.isoformat() if value else None


def _uploaded_file():
    return request.files.get("file") or request.files.get("csv")


def _import_mode():
    mode = request.form.get("mode") or "upsert"
    if mode not in {"append", "upsert"}:
        raise ValueError("导入模式只能是 append 或 upsert")
    return mode


def _handle_import(import_func):
    try:
        return ok(import_func())
    except ValueError as exc:
        return fail(str(exc))


def _build_excel_template(headers):
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "template"
    sheet.append(headers)
    output = BytesIO()
    workbook.save(output)
    return output.getvalue()


def _parse_bool_query(value):
    if value is None or value == "":
        return None
    return value.lower() in {"1", "true", "yes", "on"}


def _list_teachers_by_flag(flag):
    query = Teacher.query.filter_by(status="active")
    keyword = (request.args.get("keyword") or "").strip()
    major = (request.args.get("major") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter((Teacher.name.like(like)) | (Teacher.teacher_no.like(like)))
    if major:
        query = query.filter(Teacher.major_name == major)
    return [
        item
        for item in query.order_by(Teacher.id.asc()).all()
        if flag in item.role_flag_list
    ]


def _validate_task_type_payload(data, creating):
    if creating and not data.get("type_code"):
        return "任务类别编码不能为空"
    if creating and not data.get("type_name"):
        return "任务类别名称不能为空"
    if "status" in data and data["status"] not in {"enabled", "disabled"}:
        return "任务类别状态只能是 enabled 或 disabled"
    return None


def _student_summary(student):
    return {
        "id": student.id,
        "student_no": student.student_no,
        "name": student.name,
        "college": student.college,
        "major": student.major,
        "class_name": student.class_name,
        "grade": student.grade,
    }


def _teacher_summary(teacher):
    return {
        "id": teacher.id,
        "teacher_no": teacher.teacher_no,
        "name": teacher.name,
        "college": None,
        "major": teacher.major_name,
        "role_flags": teacher.role_flag_list,
    }
