from flask import request
from flask_login import login_required

from app.core.responses import ok
from app.core.validation import parse_bool_query
from app.models.teacher import Teacher
from app.modules.api.blueprint import api_bp
from app.modules.api.serializers import teacher_summary
from app.services.task_type_service import list_task_types, task_type_to_dict
from app.utils.permissions import role_required


@api_bp.route("/task-types")
@login_required
def get_task_types():
    enabled = parse_bool_query(request.args.get("enabled"))
    return ok(
        {"items": [task_type_to_dict(item) for item in list_task_types(enabled=enabled)]}
    )


@api_bp.route("/teachers/advisors")
@login_required
def get_advisors():
    return ok(
        {
            "items": [
                teacher_summary(item) for item in _list_teachers_by_flag("advisor")
            ]
        }
    )


@api_bp.route("/admin/reviewers")
@login_required
@role_required("admin")
def admin_get_reviewers():
    return ok(
        {
            "items": [
                teacher_summary(item)
                for item in _list_teachers_by_flag("reviewer")
            ]
        }
    )


@api_bp.route("/admin/task-types", methods=["GET"])
@login_required
@role_required("admin")
def admin_get_task_types():
    enabled = parse_bool_query(request.args.get("enabled"))
    return ok(
        {"items": [task_type_to_dict(item) for item in list_task_types(enabled=enabled)]}
    )


def _list_teachers_by_flag(flag):
    query = Teacher.query.filter_by(status="active")
    keyword = (request.args.get("keyword") or "").strip()
    major = (request.args.get("major") or "").strip()
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            (Teacher.name.like(like)) | (Teacher.teacher_no.like(like))
        )
    if major:
        query = query.filter(Teacher.major_name == major)
    return [
        item
        for item in query.order_by(Teacher.id.asc()).all()
        if flag in item.role_flag_list
    ]
