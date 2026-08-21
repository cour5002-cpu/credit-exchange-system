from datetime import timedelta
from io import BytesIO

from flask import Response, request, send_file
from flask_login import current_user, login_required
from openpyxl import Workbook

from app.core.responses import fail, ok
from app.models.hour_application import HourApplication
from app.modules.api.blueprint import api_bp
from app.services.import_service import import_admins, import_students, import_teachers
from app.utils.permissions import role_required
from app.utils.time_utils import parse_api_datetime


@api_bp.route("/admin/import-templates/<target>")
@login_required
@role_required("admin")
def admin_import_template(target):
    templates = {
        "students": ["student_no", "name", "username", "password", "phone", "email", "college", "major", "grade", "class_name", "expected_graduation_date", "status"],
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
