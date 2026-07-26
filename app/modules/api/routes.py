from io import BytesIO

import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from flask import Blueprint, Response, current_app, jsonify, request, send_file
from flask_login import current_user, login_required, login_user, logout_user
from openpyxl import Workbook
from sqlalchemy.exc import IntegrityError

from app.extensions import db
from app.models.attachment import Attachment
from app.models.appeal import Appeal
from app.models.application_advisor import ApplicationAdvisor
from app.models.credit_exchange_allocation import CreditExchangeAllocation
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.college_task import CollegeTask
from app.models.complaint import Complaint
from app.models.hour_application import HourApplication
from app.models.hour_application_member import HourApplicationMember
from app.models.operation_log import OperationLog
from app.models.student import Student
from app.models.task_member import TaskMember
from app.models.task_result_submission import TaskResultSubmission
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
    close_unfinishable_application,
    create_extension_request,
    create_student_application,
    current_teacher,
    final_approve,
    final_reject,
    get_advisor_application,
    get_application,
    get_visible_extension_request,
    get_reviewer_application,
    get_visible_application_for_student,
    latest_reviewer_result,
    list_admin_hour_applications,
    list_admin_extensions,
    list_advisor_pending_extensions,
    list_advisor_material_pending,
    list_advisor_pending,
    list_pending_assignment,
    list_pending_final,
    list_reviewer_pending,
    list_student_hour_applications,
    reviewer_approve,
    reviewer_reject,
    review_extension_request,
    submit_materials,
)
from app.services.week4_credit_exchange_service import (
    admin_batch_final_approve_credit_exchanges,
    admin_final_approve_credit_exchange,
    admin_final_reject_credit_exchange,
    advisor_approve_credit_exchange,
    advisor_reject_credit_exchange,
    create_conversion_rule,
    create_rule_file,
    current_conversion_rule,
    get_admin_credit_exchange,
    get_advisor_credit_exchange,
    get_exchange_form_data,
    get_rule_file,
    get_student_credit_exchange,
    list_admin_pending_final_credit_exchanges,
    list_advisor_pending_credit_exchanges,
    list_available_hour_awards,
    list_conversion_rules,
    list_rule_files,
    list_student_credit_exchanges,
    set_conversion_rule_status,
    submit_credit_exchange,
    update_conversion_rule,
)
from app.services.week5_appeal_task_service import (
    admin_approve_appeal,
    admin_approve_task_publish,
    admin_reject_appeal,
    admin_reject_task_publish,
    create_appeal,
    create_complaint,
    create_task,
    get_appealable_target,
    get_admin_appeal,
    get_admin_task,
    get_advisor_task,
    get_advisor_task_result,
    get_complaint,
    get_reviewer_appeal,
    get_student_appeal,
    get_student_registration,
    get_student_task,
    list_admin_appeals,
    list_admin_tasks,
    list_complaints,
    list_reopened_pending_advisor,
    list_reopened_pending_assignment,
    list_reviewer_appeals,
    list_advisor_tasks,
    list_my_tasks,
    list_pending_task_publish_requests,
    list_student_appeals,
    list_student_tasks,
    list_task_registrations_for_advisor,
    register_task,
    assign_reopened_appeal,
    assign_task_leader,
    advisor_reconfirm_appeal,
    get_student_team,
    review_reopened_appeal,
    review_task_result,
    resubmit_task_result,
    selected_task_members,
    select_task_registrations,
    submit_task_result,
)
from app.utils.permissions import role_required
from app.utils.time_utils import business_now, format_api_datetime, parse_api_datetime, system_time_payload


api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.route("/system/time")
def get_system_time():
    return ok(system_time_payload())


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
    item = db.get_or_404(TaskType, task_type_id)
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
    item = db.get_or_404(TaskType, task_type_id)
    return ok(task_type_to_dict(set_task_type_status(item, "enabled")))


@api_bp.route("/admin/task-types/<int:task_type_id>/disable", methods=["POST"])
@login_required
@role_required("admin")
def admin_disable_task_type(task_type_id):
    item = db.get_or_404(TaskType, task_type_id)
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
    allowed_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt"}
    extension = os.path.splitext(file_storage.filename)[1].lower()
    if extension not in allowed_extensions:
        return fail("附件类型不支持")
    upload_root = current_app.config["UPLOAD_FOLDER"]
    attachment_dir = os.path.join(upload_root, "attachments", biz_type)
    os.makedirs(attachment_dir, exist_ok=True)
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
    if not _can_access_attachment(attachment):
        return fail("无权访问该附件", code=40301, status=403)
    if _parse_bool_query(request.args.get("download")):
        path = os.path.join(current_app.root_path, attachment.file_path)
        return send_file(path, as_attachment=True, download_name=attachment.file_name)
    return ok(_attachment_summary(attachment))


@api_bp.route("/attachments/<int:attachment_id>", methods=["DELETE"])
@login_required
def delete_attachment(attachment_id):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment or attachment.status != "active":
        return fail("附件不存在", code=40401, status=404)
    data = request.get_json(silent=True) or {}
    bound_to_draft = _attachment_bound_to_draft(attachment)
    uploader_can_delete = attachment.uploaded_by == current_user.id and (
        not attachment.owner_id or bound_to_draft
    )
    if uploader_can_delete:
        action = "delete"
        attachment.status = "deleted"
        reason = (data.get("reason") or "上传者删除未绑定或草稿附件").strip()
    elif current_user.has_role("admin"):
        reason = (data.get("reason") or "").strip()
        if not reason:
            return fail("管理员作废已提交附件时必须填写原因")
        action = "void"
        attachment.status = "voided"
    elif attachment.uploaded_by == current_user.id:
        return fail("正式提交后的附件不能由上传者删除", code=40901, status=409)
    else:
        return fail("无权作废该附件", code=40301, status=403)
    attachment.voided_by = current_user.id
    attachment.voided_at = business_now()
    attachment.void_reason = reason
    db.session.add(OperationLog(
        user_id=current_user.id,
        module="attachment",
        biz_type="attachment",
        biz_id=attachment.id,
        action=action,
        detail=reason,
    ))
    db.session.commit()
    return ok(_attachment_summary(attachment))


@api_bp.route("/admin/attachments/<int:attachment_id>/operation-records", methods=["GET"])
@login_required
@role_required("admin")
def admin_attachment_operation_records(attachment_id):
    attachment = db.session.get(Attachment, attachment_id)
    if not attachment:
        return fail("附件不存在", code=40401, status=404)
    def payload():
        page, page_size = _pagination_args()
        result = _paginate_operation_records(
            OperationLog.query.filter_by(biz_type="attachment", biz_id=attachment.id).order_by(OperationLog.id.desc()),
            page,
            page_size,
        )
        return ok({
            "attachment": _attachment_summary(attachment),
            "items": [_operation_record_summary(item) for item in result.items],
            "page": result.page,
            "page_size": result.page_size,
            "total": result.total,
            "pages": result.pages,
        })
    return _handle_business(payload)


@api_bp.route("/admin/exports/hour-applications", methods=["GET"])
@login_required
@role_required("admin")
def admin_export_hour_applications():
    query = HourApplication.query
    status = (request.args.get("status") or "").strip()
    if status:
        query = query.filter_by(status=status)
    try:
        date_from = parse_api_datetime(request.args["date_from"]) if request.args.get("date_from") else None
        date_to = parse_api_datetime(request.args["date_to"]) if request.args.get("date_to") else None
    except (TypeError, ValueError):
        return fail("日期格式必须为 YYYY-MM-DD")
    if date_from:
        query = query.filter(HourApplication.created_at >= date_from)
    if date_to:
        query = query.filter(HourApplication.created_at < date_to.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1))
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "课时申请"
    sheet.append(["申请编号", "标题", "申请类型", "来源", "申请课时", "状态", "创建时间"])
    for item in query.order_by(HourApplication.id.asc()).all():
        sheet.append([
            item.application_no,
            item.title,
            item.application_type,
            item.source_type,
            float(item.requested_hours),
            item.status,
            item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else "",
        ])
    stream = BytesIO()
    workbook.save(stream)
    stream.seek(0)
    return send_file(
        stream,
        as_attachment=True,
        download_name="hour-applications.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@api_bp.route("/admin/rule-files", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_rule_file():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_rule_file_summary(create_rule_file(current_user, data))))


@api_bp.route("/rule-files", methods=["GET"])
@login_required
def api_rule_files():
    keyword = (request.args.get("keyword") or "").strip() or None
    rule_type = (request.args.get("rule_type") or "").strip() or None
    usage_type = (request.args.get("usage_type") or "").strip() or None
    return _handle_business(lambda: ok({"items": [_rule_file_summary(item) for item in list_rule_files(keyword, rule_type, usage_type)]}))


@api_bp.route("/rule-files/<int:rule_file_id>/download", methods=["GET"])
@login_required
def api_download_rule_file(rule_file_id):
    rule_file = get_rule_file(rule_file_id)
    attachment = rule_file.attachment
    path = os.path.join(current_app.root_path, attachment.file_path)
    return send_file(path, as_attachment=True, download_name=attachment.file_name)


@api_bp.route("/admin/credit-conversion-rules", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_conversion_rule():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok({"rule": _conversion_rule_summary(create_conversion_rule(current_user, data))}))


@api_bp.route("/admin/credit-conversion-rules", methods=["GET"])
@login_required
@role_required("admin")
def admin_conversion_rules():
    status = (request.args.get("status") or "").strip() or None
    keyword = (request.args.get("keyword") or "").strip() or None
    return _handle_business(lambda: ok({"items": [_conversion_rule_summary(item) for item in list_conversion_rules(status, keyword)]}))


@api_bp.route("/credit-conversion-rules/current", methods=["GET"])
@login_required
def api_current_conversion_rule():
    return _handle_business(lambda: ok({"rule": _conversion_rule_summary(current_conversion_rule())}))


@api_bp.route("/admin/credit-conversion-rules/<int:rule_id>", methods=["PATCH"])
@login_required
@role_required("admin")
def admin_update_conversion_rule(rule_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok({"rule": _conversion_rule_summary(update_conversion_rule(current_user, rule_id, data))}))


@api_bp.route("/admin/credit-conversion-rules/<int:rule_id>/enable", methods=["POST"])
@login_required
@role_required("admin")
def admin_enable_conversion_rule(rule_id):
    return _handle_business(lambda: ok({"rule": _conversion_rule_summary(set_conversion_rule_status(current_user, rule_id, "active"))}))


@api_bp.route("/admin/credit-conversion-rules/<int:rule_id>/disable", methods=["POST"])
@login_required
@role_required("admin")
def admin_disable_conversion_rule(rule_id):
    return _handle_business(lambda: ok({"rule": _conversion_rule_summary(set_conversion_rule_status(current_user, rule_id, "inactive"))}))


@api_bp.route("/student/hour-applications", methods=["POST"])
@login_required
@role_required("student")
def student_submit_hour_application():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_application_created_payload(create_student_application(current_user, data, submit=True))))


@api_bp.route("/student/hour-applications/drafts", methods=["POST"])
@login_required
@role_required("student")
def student_save_hour_application_draft():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_application_created_payload(create_student_application(current_user, data, submit=False))))


@api_bp.route("/student/hour-applications", methods=["GET"])
@login_required
@role_required("student")
def student_hour_applications():
    status = (request.args.get("status") or "").strip() or None
    role = (request.args.get("role") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_student_hour_applications(current_user, status, role, page, page_size),
        _hour_application_summary,
    ))


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


@api_bp.route("/student/hour-applications/<int:application_id>/extension-requests", methods=["POST"])
@login_required
@role_required("student")
def student_create_extension_request(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_extension_created_payload(create_extension_request(current_user, application_id, data))))


@api_bp.route("/advisor/hour-applications/pending", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_pending_hour_applications():
    status = (request.args.get("status") or "submitted").strip()
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_advisor_pending(current_user, status, page, page_size),
        _hour_application_summary,
    ))


@api_bp.route("/advisor/hour-applications/materials/pending", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_pending_materials():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_advisor_material_pending(current_user, page, page_size),
        _hour_application_summary,
    ))


@api_bp.route("/advisor/extension-requests/pending", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_pending_extension_requests():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_advisor_pending_extensions(current_user, page, page_size),
        _extension_request_payload,
    ))


@api_bp.route("/extension-requests/<int:extension_request_id>", methods=["GET"])
@login_required
def extension_request_detail(extension_request_id):
    return _handle_business(lambda: ok(_extension_detail_payload(get_visible_extension_request(current_user, extension_request_id))))


@api_bp.route("/advisor/extension-requests/<int:extension_request_id>/approve", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_approve_extension_request(extension_request_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_extension_review_payload(*review_extension_request(current_user, extension_request_id, True, data.get("comment"), "advisor"))))


@api_bp.route("/advisor/extension-requests/<int:extension_request_id>/reject", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_reject_extension_request(extension_request_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_extension_review_payload(*review_extension_request(current_user, extension_request_id, False, data.get("comment"), "advisor"))))


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
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_admin_hour_applications(status, application_type, keyword, page, page_size),
        _admin_hour_application_summary,
    ))


@api_bp.route("/admin/extension-requests", methods=["GET"])
@login_required
@role_required("admin")
def admin_extension_requests():
    return _handle_business(lambda: ok({"items": [_extension_request_payload(item) for item in list_admin_extensions()]}))


@api_bp.route("/admin/extension-requests/pending-special", methods=["GET"])
@login_required
@role_required("admin")
def admin_pending_special_extension_requests():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_admin_extensions(pending_special=True, page=page, page_size=page_size),
        _extension_request_payload,
    ))


@api_bp.route("/admin/extension-requests/<int:extension_request_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def admin_approve_extension_request(extension_request_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_extension_review_payload(*review_extension_request(current_user, extension_request_id, True, data.get("comment"), "admin"))))


@api_bp.route("/admin/extension-requests/<int:extension_request_id>/reject", methods=["POST"])
@login_required
@role_required("admin")
def admin_reject_extension_request(extension_request_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_extension_review_payload(*review_extension_request(current_user, extension_request_id, False, data.get("comment"), "admin"))))


@api_bp.route("/admin/hour-applications/<int:application_id>/close", methods=["POST"])
@login_required
@role_required("admin")
def admin_close_hour_application(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(close_unfinishable_application(current_user, application_id, data.get("reason")))))


@api_bp.route("/admin/hour-applications/pending-assignment", methods=["GET"])
@login_required
@role_required("admin")
def admin_pending_assignment():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_pending_assignment(page, page_size),
        _hour_application_summary,
    ))


@api_bp.route("/admin/hour-applications/pending-final", methods=["GET"])
@login_required
@role_required("admin")
def admin_pending_final():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_pending_final(page, page_size),
        _pending_final_summary,
    ))


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
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_reviewer_pending(current_user, page, page_size),
        _hour_application_summary,
    ))


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


@api_bp.route("/student/credit-exchanges/available-hour-awards", methods=["GET"])
@login_required
@role_required("student")
def student_available_hour_awards():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_available_hour_awards(current_user, page, page_size),
        _hour_award_summary,
    ))


@api_bp.route("/student/credit-exchanges/form-data", methods=["GET"])
@login_required
@role_required("student")
def student_credit_exchange_form_data():
    hour_award_record_id = request.args.get("hour_award_record_id")
    return _handle_business(lambda: ok(_credit_exchange_form_payload(*get_exchange_form_data(current_user, hour_award_record_id))))


@api_bp.route("/student/credit-exchanges/drafts", methods=["POST"])
@login_required
@role_required("student")
def student_save_credit_exchange_draft():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_credit_exchange_created_payload(submit_credit_exchange(current_user, data, submit=False))))


@api_bp.route("/student/credit-exchanges", methods=["POST"])
@login_required
@role_required("student")
def student_submit_credit_exchange():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_credit_exchange_created_payload(submit_credit_exchange(current_user, data, submit=True))))


@api_bp.route("/student/credit-exchanges", methods=["GET"])
@login_required
@role_required("student")
def student_credit_exchanges():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_student_credit_exchanges(current_user, status, page, page_size),
        _credit_exchange_summary,
    ))


@api_bp.route("/student/credit-exchanges/<int:exchange_id>", methods=["GET"])
@login_required
@role_required("student")
def student_credit_exchange_detail(exchange_id):
    return _handle_business(lambda: ok(_credit_exchange_detail_payload(get_student_credit_exchange(current_user, exchange_id))))


@api_bp.route("/advisor/credit-exchanges/pending", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_pending_credit_exchanges():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_advisor_pending_credit_exchanges(current_user, page, page_size),
        _credit_exchange_summary,
    ))


@api_bp.route("/advisor/credit-exchanges/<int:exchange_id>", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_credit_exchange_detail(exchange_id):
    return _handle_business(lambda: ok(_credit_exchange_detail_payload(get_advisor_credit_exchange(current_user, exchange_id))))


@api_bp.route("/advisor/credit-exchanges/<int:exchange_id>/approve", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_approve_credit_exchange_api(exchange_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(advisor_approve_credit_exchange(current_user, exchange_id, data.get("comment")))))


@api_bp.route("/advisor/credit-exchanges/<int:exchange_id>/reject", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_reject_credit_exchange_api(exchange_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(advisor_reject_credit_exchange(current_user, exchange_id, data.get("comment")))))


@api_bp.route("/admin/credit-exchanges/pending-final", methods=["GET"])
@login_required
@role_required("admin")
def admin_pending_final_credit_exchanges():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_admin_pending_final_credit_exchanges(page, page_size),
        _credit_exchange_summary,
    ))


@api_bp.route("/admin/credit-exchanges/<int:exchange_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_credit_exchange_detail(exchange_id):
    return _handle_business(lambda: ok(_credit_exchange_detail_payload(get_admin_credit_exchange(exchange_id))))


@api_bp.route("/admin/credit-exchanges/<int:exchange_id>/final-approve", methods=["POST"])
@login_required
@role_required("admin")
def admin_final_approve_credit_exchange_api(exchange_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_credit_exchange_final_payload(*admin_final_approve_credit_exchange(current_user, exchange_id, data.get("comment")))))


@api_bp.route("/admin/credit-exchanges/<int:exchange_id>/final-reject", methods=["POST"])
@login_required
@role_required("admin")
def admin_final_reject_credit_exchange_api(exchange_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(admin_final_reject_credit_exchange(current_user, exchange_id, data.get("comment")))))


@api_bp.route("/admin/credit-exchanges/batch-approve", methods=["POST"])
@login_required
@role_required("admin")
def admin_batch_approve_credit_exchange_api():
    data = request.get_json(silent=True) or {}
    def payload():
        items = admin_batch_final_approve_credit_exchanges(
            current_user,
            data.get("ids") or data.get("exchange_ids"),
            data.get("comment"),
        )
        return ok({
            "items": items,
            "success_count": sum(1 for item in items if item["success"]),
            "failed_count": sum(1 for item in items if not item["success"]),
        })
    return _handle_business(payload)


@api_bp.route("/student/appeals", methods=["POST"])
@login_required
@role_required("student")
def student_create_appeal():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_appeal_created_payload(create_appeal(current_user, data))))


@api_bp.route("/student/appealable-targets/<target_type>/<int:target_id>", methods=["GET"])
@login_required
@role_required("student")
def student_appealable_target(target_type, target_id):
    def payload():
        target, can_appeal, reason = get_appealable_target(current_user, target_type, target_id)
        summary = _hour_application_summary(target) if target_type == "hour_application" else _credit_exchange_summary(target)
        return ok({"target": summary, "can_appeal": can_appeal, "reason": reason})
    return _handle_business(payload)


@api_bp.route("/student/appeals", methods=["GET"])
@login_required
@role_required("student")
def student_appeals():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_student_appeals(current_user, status, page, page_size),
        _appeal_summary,
    ))


@api_bp.route("/student/appeals/<int:appeal_id>", methods=["GET"])
@login_required
@role_required("student")
def student_appeal_detail(appeal_id):
    return _handle_business(lambda: ok(_appeal_detail_payload(get_student_appeal(current_user, appeal_id))))


@api_bp.route("/admin/appeals", methods=["GET"])
@login_required
@role_required("admin")
def admin_appeals():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_admin_appeals(status, page, page_size),
        _appeal_summary,
    ))


@api_bp.route("/admin/appeals/<int:appeal_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_appeal_detail(appeal_id):
    return _handle_business(lambda: ok(_appeal_detail_payload(get_admin_appeal(appeal_id))))


@api_bp.route("/admin/appeals/<int:appeal_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def admin_approve_appeal_api(appeal_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_appeal_review_payload(*admin_approve_appeal(current_user, appeal_id, data.get("admin_advice")))))


@api_bp.route("/admin/appeals/<int:appeal_id>/reject", methods=["POST"])
@login_required
@role_required("admin")
def admin_reject_appeal_api(appeal_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_appeal_created_payload(admin_reject_appeal(current_user, appeal_id, data.get("admin_advice")))))


@api_bp.route("/advisor/appeals/reopened/pending-confirmation", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_reopened_appeals():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_reopened_pending_advisor(current_user, page, page_size),
        _appeal_summary,
    ))


@api_bp.route("/advisor/appeals/<int:appeal_id>/reconfirm", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_reconfirm_appeal_api(appeal_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_reopened_appeal_payload(*advisor_reconfirm_appeal(current_user, appeal_id, data.get("decision"), data.get("comment")))))


@api_bp.route("/admin/appeals/reopened/pending-assignment", methods=["GET"])
@login_required
@role_required("admin")
def admin_reopened_pending_assignment():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_reopened_pending_assignment(page, page_size),
        _appeal_summary,
    ))


@api_bp.route("/admin/appeals/<int:appeal_id>/assign-reviewer", methods=["POST"])
@login_required
@role_required("admin")
def admin_assign_reopened_appeal(appeal_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_reopened_appeal_payload(*assign_reopened_appeal(current_user, appeal_id, data.get("reviewer_teacher_id"), data.get("comment")))))


@api_bp.route("/reviewer/appeal-reviews", methods=["GET"])
@login_required
@role_required("reviewer")
def reviewer_appeal_reviews():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_reviewer_appeals(current_user, page, page_size),
        _appeal_summary,
    ))


@api_bp.route("/reviewer/appeal-reviews/<int:appeal_id>", methods=["GET"])
@login_required
@role_required("reviewer")
def reviewer_appeal_review_detail(appeal_id):
    return _handle_business(lambda: ok(_appeal_detail_payload(get_reviewer_appeal(current_user, appeal_id))))


def _review_appeal_response(appeal_id, decision):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_reopened_appeal_payload(*review_reopened_appeal(
        current_user, appeal_id, decision, data.get("comment"), data.get("reviewer_suggested_hours")
    ))))


@api_bp.route("/reviewer/appeal-reviews/<int:appeal_id>/approve", methods=["POST"])
@login_required
@role_required("reviewer")
def reviewer_approve_appeal_review(appeal_id):
    return _review_appeal_response(appeal_id, "approve")


@api_bp.route("/reviewer/appeal-reviews/<int:appeal_id>/modified-approve", methods=["POST"])
@login_required
@role_required("reviewer")
def reviewer_modified_approve_appeal_review(appeal_id):
    return _review_appeal_response(appeal_id, "modified_approve")


@api_bp.route("/reviewer/appeal-reviews/<int:appeal_id>/reject", methods=["POST"])
@login_required
@role_required("reviewer")
def reviewer_reject_appeal_review(appeal_id):
    return _review_appeal_response(appeal_id, "reject")


@api_bp.route("/admin/tasks/drafts", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_task_draft():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(create_task(current_user, data, "admin", submit=False))))


@api_bp.route("/admin/tasks", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_task():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(create_task(current_user, data, "admin", submit=True))))


@api_bp.route("/admin/tasks", methods=["GET"])
@login_required
@role_required("admin")
def admin_tasks():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_admin_tasks(status, page, page_size),
        _task_summary,
    ))


@api_bp.route("/admin/tasks/<int:task_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_task_detail(task_id):
    return _handle_business(lambda: ok(_task_detail_payload(get_admin_task(task_id))))


@api_bp.route("/advisor/tasks/drafts", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_create_task_draft():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(create_task(current_user, data, "teacher", submit=False))))


@api_bp.route("/advisor/tasks", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_create_task():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(create_task(current_user, data, "teacher", submit=True))))


@api_bp.route("/advisor/tasks", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_tasks():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: ok({"items": [_task_summary(item) for item in list_advisor_tasks(current_user, status)]}))


@api_bp.route("/advisor/tasks/<int:task_id>", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_task_detail(task_id):
    return _handle_business(lambda: ok(_task_detail_payload(get_advisor_task(current_user, task_id))))


@api_bp.route("/advisor/tasks/<int:task_id>/registrations", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_task_registrations(task_id):
    return _handle_business(lambda: ok({"items": [_task_registration_summary(item) for item in list_task_registrations_for_advisor(current_user, task_id)]}))


@api_bp.route("/advisor/tasks/<int:task_id>/registrations/select", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_select_task_registrations(task_id):
    data = request.get_json(silent=True) or {}
    def payload():
        task = select_task_registrations(current_user, task_id, data)
        selected_count = TaskMember.query.filter_by(task_id=task.id, status="active").count()
        return ok({"selected_count": selected_count, "task_status": task.status})
    return _handle_business(payload)


@api_bp.route("/advisor/tasks/<int:task_id>/selected-members", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_selected_task_members(task_id):
    def payload():
        _, members = selected_task_members(current_user, task_id)
        return ok({"items": [_task_member_summary(item) for item in members]})
    return _handle_business(payload)


@api_bp.route("/advisor/tasks/<int:task_id>/leader", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_assign_task_leader(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_leader_payload(*assign_task_leader(current_user, task_id, data.get("leader_student_id")))))


@api_bp.route("/advisor/task-result-submissions/<int:submission_id>", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_task_result_detail(submission_id):
    return _handle_business(lambda: ok(_task_result_detail_payload(get_advisor_task_result(current_user, submission_id))))


@api_bp.route("/advisor/task-result-submissions/<int:submission_id>/approve", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_approve_task_result(submission_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_result_created_payload(review_task_result(current_user, submission_id, True, data.get("comment")))))


@api_bp.route("/advisor/task-result-submissions/<int:submission_id>/reject", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_reject_task_result(submission_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_result_created_payload(review_task_result(current_user, submission_id, False, data.get("comment")))))


@api_bp.route("/student/tasks", methods=["GET"])
@login_required
@role_required("student")
def student_tasks():
    keyword = (request.args.get("keyword") or "").strip() or None
    task_type_id = (request.args.get("task_type_id") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_student_tasks(current_user, keyword, task_type_id, page, page_size),
        _task_summary,
    ))


@api_bp.route("/student/tasks/<int:task_id>", methods=["GET"])
@login_required
@role_required("student")
def student_task_detail(task_id):
    return _handle_business(lambda: ok(_student_task_detail_payload(*get_student_task(current_user, task_id))))


@api_bp.route("/student/tasks/<int:task_id>/team", methods=["GET"])
@login_required
@role_required("student")
def student_task_team(task_id):
    return _handle_business(lambda: ok(_student_team_payload(*get_student_team(current_user, task_id))))


@api_bp.route("/student/tasks/<int:task_id>/result-submissions", methods=["POST"])
@login_required
@role_required("student")
def student_submit_task_result(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_result_created_payload(submit_task_result(current_user, task_id, data))))


@api_bp.route("/student/task-result-submissions/<int:submission_id>/resubmit", methods=["POST"])
@login_required
@role_required("student")
def student_resubmit_task_result(submission_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_result_created_payload(
        resubmit_task_result(current_user, submission_id, data)
    )))


@api_bp.route("/student/tasks/<int:task_id>/registrations", methods=["POST"])
@login_required
@role_required("student")
def student_register_task(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_registration_created_payload(register_task(current_user, task_id, data))))


@api_bp.route("/student/my-tasks", methods=["GET"])
@login_required
@role_required("student")
def student_my_tasks():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: ok({"items": [_task_summary(item) for item in list_my_tasks(current_user, status)]}))


@api_bp.route("/student/task-registrations/<int:registration_id>", methods=["GET"])
@login_required
@role_required("student")
def student_task_registration_detail(registration_id):
    registration = get_student_registration(current_user, registration_id)
    return _handle_business(lambda: ok({"registration": _task_registration_summary(registration), "status": registration.status}))


@api_bp.route("/admin/task-publish-requests", methods=["GET"])
@login_required
@role_required("admin")
def admin_task_publish_requests():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_pending_task_publish_requests(page, page_size),
        _task_summary,
    ))


@api_bp.route("/admin/task-publish-requests/<int:task_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_task_publish_request_detail(task_id):
    return _handle_business(lambda: ok(_task_detail_payload(get_admin_task(task_id))))


@api_bp.route("/admin/task-publish-requests/<int:task_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def admin_approve_task_publish_api(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(admin_approve_task_publish(current_user, task_id, data.get("comment")))))


@api_bp.route("/admin/task-publish-requests/<int:task_id>/reject", methods=["POST"])
@login_required
@role_required("admin")
def admin_reject_task_publish_api(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(admin_reject_task_publish(current_user, task_id, data.get("comment")))))


@api_bp.route("/student/complaints", methods=["POST"])
@login_required
@role_required("student")
def student_create_complaint():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_complaint_summary(create_complaint(current_user, data))))


@api_bp.route("/admin/complaints", methods=["GET"])
@login_required
@role_required("admin")
def admin_complaints():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_complaints(status, page, page_size),
        _complaint_summary,
    ))


@api_bp.route("/admin/complaints/<int:complaint_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_complaint_detail(complaint_id):
    return _handle_business(lambda: ok(_complaint_detail_payload(get_complaint(complaint_id, mark_viewed=True))))


@api_bp.route("/operation-records", methods=["GET"])
@login_required
@role_required("advisor", "reviewer", "admin")
def operation_records():
    role_scope = (request.args.get("role_scope") or "").strip()
    if role_scope not in {"advisor", "reviewer", "admin"} or not current_user.has_role(role_scope):
        return fail("role_scope 与当前用户角色不匹配", code=40301, status=403)
    query = OperationLog.query.filter_by(user_id=current_user.id)
    biz_type = (request.args.get("biz_type") or "").strip()
    if biz_type:
        query = query.filter_by(biz_type=biz_type)
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: _paginate_operation_records(query.order_by(OperationLog.id.desc()), page, page_size),
        _operation_record_summary,
    ))


@api_bp.route("/operation-records/<int:record_id>", methods=["GET"])
@login_required
@role_required("advisor", "reviewer", "admin")
def operation_record_detail(record_id):
    record = OperationLog.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        return fail("处理记录不存在或无权查看", code=40401, status=404)
    return ok({"record": _operation_record_summary(record), "target": _operation_target_summary(record)})


def ok(data=None):
    return jsonify({"code": 0, "message": "success", "data": data or {}})


def _pagination_args():
    try:
        page = int(request.args.get("page", 1))
        page_size = int(request.args.get("page_size", 20))
    except (TypeError, ValueError):
        raise BusinessError("page 和 page_size 必须是整数")
    if page < 1:
        raise BusinessError("page 必须大于等于 1")
    if page_size < 1 or page_size > 100:
        raise BusinessError("page_size 必须在 1 到 100 之间")
    return page, page_size


def _paged_response(loader, serializer):
    page, page_size = _pagination_args()
    result = loader(page, page_size)
    return ok({
        "items": [serializer(item) for item in result.items],
        "page": result.page,
        "page_size": result.page_size,
        "total": result.total,
        "pages": result.pages,
    })


def _paginate_operation_records(query, page, page_size):
    from app.utils.pagination import paginate_query
    return paginate_query(query, page, page_size)


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


def _extension_created_payload(extension):
    application = extension.application
    applicant = application.applicant or application.student
    return {
        "extension_request_id": extension.id,
        "applicant": _student_summary(applicant),
        "applicant_name": applicant.name,
        "status": application.status,
        "review_level": extension.review_level,
    }


def _extension_review_payload(extension, result_status):
    return {"id": extension.id, "status": result_status}


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


def _credit_exchange_final_payload(application, record):
    return {"id": application.id, "status": application.status, "credit_exchange_record_id": record.id}


def _credit_exchange_created_payload(application):
    payload = {
        "id": application.id,
        "status": application.status,
    }
    if application.rule_id:
        payload["calculated_allocations"] = [_credit_allocation_summary(item) for item in application.allocations]
    return payload


def _appeal_created_payload(appeal):
    return {"id": appeal.id, "appeal_no": appeal.appeal_no, "status": appeal.status}


def _appeal_review_payload(appeal, target):
    return {
        "id": appeal.id,
        "status": appeal.status,
        "next_step": "pending_advisor_reconfirm",
        "target_status": target.status,
    }


def _task_created_payload(task):
    return {"id": task.id, "task_no": task.task_no, "status": task.status}


def _task_registration_created_payload(registration):
    return {"registration_id": registration.id, "status": registration.status}


def _rule_file_summary(rule_file):
    if not rule_file:
        return None
    return {
        "id": rule_file.id,
        "title": rule_file.title,
        "description": rule_file.description,
        "rule_type": rule_file.rule_type,
        "usage_type": rule_file.usage_type,
        "attachment_id": rule_file.attachment_id,
        "attachment": _attachment_summary(rule_file.attachment) if rule_file.attachment else None,
        "version_no": rule_file.version_no,
        "status": rule_file.status,
        "created_at": _iso(rule_file.created_at),
        "updated_at": _iso(rule_file.updated_at),
    }


def _conversion_rule_summary(rule):
    if not rule:
        return None
    return {
        "id": rule.id,
        "rule_id": rule.id,
        "rule_name": rule.rule_name,
        "hours_per_credit": _number(rule.hours_per_credit),
        "max_single_exchange_hours": _number(rule.max_single_exchange_hours),
        "rounding_mode": rule.rounding_mode,
        "effective_at": _iso(rule.effective_at),
        "expires_at": _iso(rule.expires_at),
        "rule_file_id": rule.rule_file_id,
        "rule_file": _rule_file_summary(rule.rule_file) if rule.rule_file else None,
        "status": rule.status,
        "created_at": _iso(rule.created_at),
        "updated_at": _iso(rule.updated_at),
    }


def _hour_award_summary(award):
    application = award.application
    return {
        "id": award.id,
        "hour_award_record_id": award.id,
        "application_id": award.application_id,
        "application_no": application.application_no if application else None,
        "title": application.title if application else None,
        "leader_student_id": award.leader_student_id,
        "leader": _student_summary(award.leader) if award.leader else None,
        "total_hours": _number(award.total_hours),
        "source_type": award.source_type,
        "is_exchanged": bool(award.is_exchanged),
        "awarded_at": _iso(award.awarded_at),
        "remark": award.remark,
    }


def _credit_exchange_form_payload(award, members, rule, suggested_total_credits, can_submit):
    return {
        "hour_award": _hour_award_summary(award),
        "members": [
            {
                "student": _student_summary(item.student),
                "is_leader": bool(item.is_leader),
                "can_apply_credit_exchange": bool(item.can_apply_credit_exchange),
            }
            for item in members
        ],
        "conversion_rule": _conversion_rule_summary(rule),
        "suggested_total_credits": _number(suggested_total_credits),
        "can_submit": bool(can_submit),
    }


def _credit_exchange_summary(exchange):
    applicant = exchange.applicant or exchange.student
    return {
        "id": exchange.id,
        "exchange_no": exchange.exchange_no,
        "hour_award_record_id": exchange.hour_award_record_id,
        "hour_application_id": exchange.hour_application_id,
        "applicant": _student_summary(applicant) if applicant else None,
        "advisor": _teacher_summary(exchange.advisor) if exchange.advisor else None,
        "total_hours": _number(exchange.total_hours or exchange.requested_hours),
        "estimated_total_credits": _number(exchange.estimated_total_credits or exchange.estimated_credits),
        "status": exchange.status,
        "status_name": exchange.status_name,
        "rule_id": exchange.rule_id,
        "rule_name": (exchange.rule_snapshot or {}).get("rule_name"),
        "created_at": _iso(exchange.created_at),
        "updated_at": _iso(exchange.updated_at),
    }


def _credit_exchange_detail_payload(exchange):
    return {
        "exchange": _credit_exchange_detail(exchange),
        "allocations": [_credit_allocation_summary(item) for item in exchange.allocations],
        "attachments": _credit_exchange_attachments(exchange),
        "actions": {
            "can_advisor_approve": exchange.status == "submitted",
            "can_admin_final": exchange.status == "pending_admin_final",
            "can_appeal": exchange.status in {"final_rejected", "advisor_rejected"},
        },
    }


def _credit_exchange_detail(exchange):
    item = _credit_exchange_summary(exchange)
    item.update(
        {
            "description": exchange.description,
            "hour_award": _hour_award_summary(exchange.hour_award_record) if exchange.hour_award_record else None,
            "rule_snapshot": exchange.rule_snapshot,
            "conversion_rule": _conversion_rule_summary(exchange.conversion_rule) if exchange.conversion_rule else None,
            "advisor_review_comment": exchange.advisor_review_comment,
            "advisor_reviewed_at": _iso(exchange.advisor_reviewed_at),
            "admin_review_comment": exchange.admin_review_comment or exchange.review_comment,
            "admin_reviewed_at": _iso(exchange.admin_reviewed_at or exchange.approved_at),
        }
    )
    return item


def _credit_allocation_summary(allocation):
    return {
        "id": allocation.id,
        "student": _student_summary(allocation.student) if allocation.student else None,
        "student_id": allocation.student_id,
        "allocated_hours": _number(allocation.allocated_hours),
        "credit_type": allocation.credit_type,
        "allocated_credits": _number(allocation.allocated_credits),
        "remark": allocation.remark,
    }


def _credit_exchange_attachments(exchange):
    return [
        _attachment_summary(item)
        for item in Attachment.query.filter_by(
            owner_type="credit_exchange",
            owner_id=exchange.id,
            status="active",
        ).order_by(Attachment.id.asc()).all()
    ]


def _appeal_summary(appeal):
    return {
        "id": appeal.id,
        "appeal_no": appeal.appeal_no,
        "target_type": appeal.target_type,
        "target_id": appeal.target_id,
        "student": _student_summary(appeal.applicant) if appeal.applicant else None,
        "reason": appeal.reason,
        "status": appeal.status,
        "admin_decision": appeal.admin_decision,
        "admin_advice": appeal.admin_advice,
        "reopen_stage": appeal.reopen_stage,
        "standard_rule_file": _rule_file_summary(appeal.standard_rule_file) if appeal.standard_rule_file else None,
        "submitted_at": _iso(appeal.created_at),
        "created_at": _iso(appeal.created_at),
        "reviewed_at": _iso(appeal.reviewed_at),
    }


def _reopened_appeal_payload(appeal, target):
    return {
        "appeal_id": appeal.id,
        "target_id": target.id,
        "target_status": target.status,
        "reopen_stage": appeal.reopen_stage,
    }


def _appeal_detail_payload(appeal):
    return {
        "appeal": _appeal_summary(appeal),
        "target": _appeal_target_summary(appeal),
        "attachments": _owner_attachments("appeal", appeal.id),
    }


def _appeal_target_summary(appeal):
    if appeal.target_type == "hour_application":
        target = get_application(appeal.target_id)
        return _hour_application_summary(target)
    if appeal.target_type == "credit_exchange":
        target = get_admin_credit_exchange(appeal.target_id)
        return _credit_exchange_summary(target)
    return None


def _task_summary(task):
    return {
        "id": task.id,
        "task_no": task.task_no,
        "title": task.title,
        "publisher_role": task.publisher_type,
        "publisher_name": task.publisher.real_name if task.publisher else None,
        "task_type_id": task.task_type_id,
        "task_type_name": task.task_type.type_name if task.task_type else None,
        "description": task.description,
        "requirement": task.requirement,
        "registration_deadline": _iso(task.registration_deadline),
        "status": task.status,
        "advisor": _teacher_summary(task.advisor) if task.advisor else None,
        "created_at": _iso(task.created_at),
        "updated_at": _iso(task.updated_at),
    }


def _task_leader_payload(task, leader_student_id):
    return {
        "task_id": task.id,
        "leader_student_id": leader_student_id,
        "leader_assigned": True,
        "task_status": task.status,
    }


def _student_team_payload(task, members, student):
    leader = next((item for item in members if item.is_leader), None)
    submission = task.result_submissions[0] if task.result_submissions else None
    return {
        "task": _task_detail(task),
        "members": [_task_member_summary(item) for item in members],
        "leader_student_id": leader.student_id if leader else None,
        "can_submit_result": bool(leader and leader.student_id == student.id and not submission),
        "can_resubmit_result": bool(
            leader
            and leader.student_id == student.id
            and submission
            and submission.status == "advisor_rejected"
            and task.status == "task_in_progress"
        ),
        "task_result_submission_id": submission.id if submission else None,
    }


def _task_result_created_payload(submission):
    return {
        "submission_id": submission.id,
        "hour_application_id": submission.hour_application_id,
        "status": submission.hour_application.status if submission.hour_application else submission.status,
        "submission_status": submission.status,
    }


def _task_result_detail_payload(submission):
    latest_version = submission.versions[-1] if submission.versions else None
    current_attachment_ids = set(latest_version.attachment_ids or []) if latest_version else set()
    return {
        "submission": {
            "id": submission.id,
            "task_id": submission.task_id,
            "leader_student_id": submission.leader_student_id,
            "summary": submission.summary,
            "requested_hours": _number(submission.requested_hours),
            "status": submission.status,
            "hour_application_id": submission.hour_application_id,
            "advisor_comment": submission.advisor_comment,
            "created_at": _iso(submission.created_at),
            "advisor_reviewed_at": _iso(submission.advisor_reviewed_at),
        },
        "task": _task_detail(submission.task),
        "attachments": [
            item for item in _owner_attachments("task_result", submission.id)
            if not current_attachment_ids or item["id"] in current_attachment_ids
        ],
        "versions": [
            {
                "id": version.id,
                "version_no": version.version_no,
                "summary": version.summary,
                "requested_hours": _number(version.requested_hours),
                "attachment_ids": version.attachment_ids or [],
                "submitted_by": version.submitted_by,
                "submitted_at": _iso(version.created_at),
            }
            for version in submission.versions
        ],
    }


def _complaint_summary(complaint):
    # V1 对管理员保持匿名：响应中不返回提交账号或学生信息。
    return {
        "id": complaint.id,
        "content": complaint.content,
        "status": complaint.status,
        "created_at": _iso(complaint.created_at),
        "viewed_at": _iso(complaint.viewed_at),
    }


def _complaint_detail_payload(complaint):
    return {
        "complaint": _complaint_summary(complaint),
        "attachments": _owner_attachments("complaint", complaint.id),
    }


def _operation_record_summary(record):
    return {
        "id": record.id,
        "module": record.module,
        "biz_type": record.biz_type,
        "biz_id": record.biz_id,
        "action": record.action,
        "detail": record.detail,
        "created_at": _iso(record.created_at),
    }


def _operation_target_summary(record):
    if not record.biz_id:
        return None
    if record.biz_type in {"hour_application", "extension_request"}:
        item = db.session.get(HourApplication, record.biz_id)
        return _hour_application_summary(item) if item else None
    if record.biz_type in {"college_task", "task_registration"}:
        item = db.session.get(CollegeTask, record.biz_id)
        return _task_summary(item) if item else None
    if record.biz_type == "task_result":
        item = db.session.get(TaskResultSubmission, record.biz_id)
        return _task_result_detail_payload(item)["submission"] if item else None
    if record.biz_type == "credit_exchange":
        item = db.session.get(CreditExchangeApplication, record.biz_id)
        return _credit_exchange_summary(item) if item else None
    if record.biz_type == "appeal":
        item = db.session.get(Appeal, record.biz_id)
        return _appeal_summary(item) if item else None
    if record.biz_type == "complaint":
        item = db.session.get(Complaint, record.biz_id)
        return _complaint_summary(item) if item else None
    return None


def _task_detail_payload(task):
    return {
        "task": _task_detail(task),
        "registrations": [_task_registration_summary(item) for item in sorted(task.registrations, key=lambda item: (item.created_at, item.id))],
        "members": [_task_member_summary(item) for item in sorted(task.members, key=lambda item: (not item.is_leader, item.id)) if item.status == "active"],
    }


def _student_task_detail_payload(task, registration):
    payload = _task_detail_payload(task)
    payload["registration"] = _task_registration_summary(registration) if registration else None
    payload["can_register"] = (
        task.status in {"published", "registration_open"}
        and registration is None
        and bool(task.registration_deadline and task.registration_deadline > business_now())
    )
    return payload


def _task_detail(task):
    item = _task_summary(task)
    members = [_task_member_summary(member) for member in task.members if member.status == "active"]
    leader = next((member for member in members if member["is_leader"]), None)
    item.update(
        {
            "major_name": task.major_name,
            "course_name": task.course_name,
            "registration_start_at": _iso(task.registration_start_at),
            "published_at": _iso(task.published_at),
            "admin_review_comment": task.admin_review_comment,
            "registrations": [_task_registration_summary(item) for item in task.registrations],
            "members": members,
            "leader": leader["student"] if leader else None,
            "actions": {
                "can_register": task.status in {"published", "registration_open"}
                and bool(task.registration_deadline and task.registration_deadline > business_now()),
                "can_select": task.status == "selection_pending",
            },
        }
    )
    return item


def _task_registration_summary(registration):
    if not registration:
        return None
    return {
        "id": registration.id,
        "task_id": registration.task_id,
        "student": _student_summary(registration.student) if registration.student else None,
        "student_id": registration.student_id,
        "status": registration.status,
        "reason": registration.apply_reason,
        "submitted_at": _iso(registration.created_at),
        "selected_at": _iso(registration.selected_at),
    }


def _task_member_summary(member):
    return {
        "id": member.id,
        "task_id": member.task_id,
        "registration_id": member.registration_id,
        "student_id": member.student_id,
        "student_name": member.student.name if member.student else None,
        "student": _student_summary(member.student) if member.student else None,
        "is_leader": bool(member.is_leader),
        "selected_at": _iso(member.created_at),
    }


def _owner_attachments(owner_type, owner_id):
    return [
        _attachment_summary(item)
        for item in Attachment.query.filter_by(owner_type=owner_type, owner_id=owner_id, status="active").order_by(Attachment.id.asc()).all()
    ]


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


def _extension_request_payload(extension):
    application = extension.application
    applicant = application.applicant or application.student
    return {
        "id": extension.id,
        "application_id": application.id,
        "applicant": _student_summary(applicant),
        "applicant_name": applicant.name,
        "old_due_at": _iso(extension.old_due_at),
        "requested_due_at": _iso(extension.requested_due_at),
        "reason": extension.reason,
        "review_level": extension.review_level,
        "status": extension.status,
        "review_comment": extension.review_comment,
        "created_at": _iso(extension.created_at),
        "reviewed_at": _iso(extension.reviewed_at),
    }


def _extension_detail_payload(extension):
    return {
        "extension_request": _extension_request_payload(extension),
        "application": _hour_application_summary(extension.application),
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
        "status": attachment.status,
        "voided_by": attachment.voided_by,
        "voided_at": _iso(attachment.voided_at),
        "void_reason": attachment.void_reason,
        "created_at": _iso(attachment.created_at),
    }


def _attachment_bound_to_draft(attachment):
    if not attachment.owner_id:
        return False
    if attachment.owner_type == "hour_application":
        owner = db.session.get(HourApplication, attachment.owner_id)
        return bool(owner and owner.status == "draft")
    if attachment.owner_type == "credit_exchange":
        owner = db.session.get(CreditExchangeApplication, attachment.owner_id)
        return bool(owner and owner.status == "draft")
    if attachment.owner_type == "college_task":
        owner = db.session.get(CollegeTask, attachment.owner_id)
        return bool(owner and owner.status == "draft")
    return False


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


def _can_access_attachment(attachment):
    if attachment.uploaded_by == current_user.id or current_user.has_role("admin"):
        return True
    if not attachment.owner_type or not attachment.owner_id:
        return False
    if attachment.owner_type == "rule_file":
        return True
    student = Student.query.filter_by(user_id=current_user.id).first()
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    if attachment.owner_type == "hour_application":
        application = db.session.get(HourApplication, attachment.owner_id)
        if not application:
            return False
        if student and (
            student.id in {application.student_id, application.applicant_student_id, application.leader_student_id}
            or HourApplicationMember.query.filter_by(application_id=application.id, student_id=student.id, status="active").first()
        ):
            return True
        return bool(teacher and (
            application.assigned_teacher_id == teacher.id
            or ApplicationAdvisor.query.filter_by(application_id=application.id, teacher_id=teacher.id).first()
        ))
    if attachment.owner_type == "task_result":
        submission = db.session.get(TaskResultSubmission, attachment.owner_id)
        if not submission:
            return False
        if student and TaskMember.query.filter_by(task_id=submission.task_id, student_id=student.id, status="active").first():
            return True
        return bool(teacher and submission.task.advisor_teacher_id == teacher.id)
    if attachment.owner_type == "credit_exchange":
        exchange = db.session.get(CreditExchangeApplication, attachment.owner_id)
        if not exchange:
            return False
        if student and (
            student.id in {exchange.student_id, exchange.applicant_student_id}
            or CreditExchangeAllocation.query.filter_by(exchange_application_id=exchange.id, student_id=student.id).first()
        ):
            return True
        return bool(teacher and exchange.advisor_teacher_id == teacher.id)
    if attachment.owner_type == "appeal":
        appeal = db.session.get(Appeal, attachment.owner_id)
        if student and appeal and appeal.applicant_student_id == student.id:
            return True
        if teacher and appeal and appeal.target_type == "hour_application":
            target = db.session.get(HourApplication, appeal.target_id)
            return bool(target and (
                target.assigned_teacher_id == teacher.id
                or ApplicationAdvisor.query.filter_by(application_id=target.id, teacher_id=teacher.id).first()
            ))
    return False


def _iso(value):
    return format_api_datetime(value)


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
        "username": teacher.user.username if teacher.user else None,
        "teacher_no": teacher.teacher_no,
        "name": teacher.name,
        "college": None,
        "major": teacher.major_name,
        "role_flags": teacher.role_flag_list,
    }
