from flask import request
from flask_login import login_required
from sqlalchemy.exc import IntegrityError

from app.core.responses import fail, ok
from app.core.validation import parse_bool_query
from app.extensions import db
from app.models.task_type import TaskType
from app.modules.api.blueprint import api_bp
from app.services.task_type_service import (
    create_task_type,
    list_task_types,
    set_task_type_status,
    task_type_to_dict,
    update_task_type,
)
from app.utils.permissions import role_required


@api_bp.route("/task-types")
@login_required
def get_task_types():
    enabled = parse_bool_query(request.args.get("enabled"))
    return ok(
        {"items": [task_type_to_dict(item) for item in list_task_types(enabled=enabled)]}
    )


@api_bp.route("/admin/task-types", methods=["GET"])
@login_required
@role_required("admin")
def admin_get_task_types():
    enabled = parse_bool_query(request.args.get("enabled"))
    return ok(
        {"items": [task_type_to_dict(item) for item in list_task_types(enabled=enabled)]}
    )


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


def _validate_task_type_payload(data, creating):
    if creating and not data.get("type_code"):
        return "任务类别编码不能为空"
    if creating and not data.get("type_name"):
        return "任务类别名称不能为空"
    if "status" in data and data["status"] not in {"enabled", "disabled"}:
        return "任务类别状态只能是 enabled 或 disabled"
    return None
