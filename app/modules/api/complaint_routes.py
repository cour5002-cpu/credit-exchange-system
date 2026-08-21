from flask import request
from flask_login import current_user, login_required

from app.core.errors import BusinessError
from app.core.responses import handle_business, ok
from app.core.validation import parse_pagination_args
from app.modules.api.blueprint import api_bp
from app.schemas.complaint import (
    admin_complaint_detail_payload,
    admin_complaint_summary,
    complaint_created_payload,
    complaint_processing_payload,
    complaint_resolved_payload,
    student_complaint_detail_payload,
    student_complaint_summary,
)
from app.services.complaint_service import (
    create_complaint,
    get_complaint,
    get_student_complaint,
    list_complaints,
    list_student_complaints,
    resolve_complaint,
    start_complaint_processing,
)
from app.utils.permissions import role_required


@api_bp.route("/student/complaints", methods=["POST"])
@login_required
@role_required("student")
def student_create_complaint():
    return handle_business(lambda: ok(complaint_created_payload(
        create_complaint(current_user, request.get_json(silent=True))
    )))


@api_bp.route("/student/complaints", methods=["GET"])
@login_required
@role_required("student")
def student_complaints():
    def action():
        page, page_size = parse_pagination_args(
            request.args.get("page", 1), request.args.get("page_size", 20)
        )
        result = list_student_complaints(
            current_user, (request.args.get("status") or "all").strip(), page, page_size
        )
        return ok({
            "items": [student_complaint_summary(item) for item in result.items],
            "page": result.page,
            "page_size": result.page_size,
            "total": result.total,
            "pages": result.pages,
        })
    return handle_business(action)


@api_bp.route("/student/complaints/<int:complaint_id>", methods=["GET"])
@login_required
@role_required("student")
def student_complaint_detail(complaint_id):
    return handle_business(lambda: ok(student_complaint_detail_payload(
        get_student_complaint(current_user, complaint_id)
    )))


@api_bp.route("/admin/complaints", methods=["GET"])
@login_required
@role_required("admin")
def admin_complaints():
    def action():
        page, page_size = parse_pagination_args(
            request.args.get("page", 1), request.args.get("page_size", 20)
        )
        result = list_complaints(
            (request.args.get("status") or "all").strip(),
            (request.args.get("category") or "").strip() or None,
            (request.args.get("keyword") or "").strip() or None,
            page,
            page_size,
        )
        return ok({
            "items": [admin_complaint_summary(item) for item in result.items],
            "page": result.page,
            "page_size": result.page_size,
            "total": result.total,
            "pages": result.pages,
        })
    return handle_business(action)


@api_bp.route("/admin/complaints/<int:complaint_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_complaint_detail(complaint_id):
    return handle_business(lambda: ok(admin_complaint_detail_payload(
        get_complaint(complaint_id, mark_viewed=True)
    )))


@api_bp.route("/admin/complaints/<int:complaint_id>/start-processing", methods=["POST"])
@login_required
@role_required("admin")
def admin_start_complaint_processing(complaint_id):
    def action():
        if request.data:
            raise BusinessError("该接口不接受请求体")
        return ok(complaint_processing_payload(start_complaint_processing(current_user, complaint_id)))
    return handle_business(action)


@api_bp.route("/admin/complaints/<int:complaint_id>/resolve", methods=["POST"])
@login_required
@role_required("admin")
def admin_resolve_complaint(complaint_id):
    return handle_business(lambda: ok(complaint_resolved_payload(
        resolve_complaint(current_user, complaint_id, request.get_json(silent=True))
    )))
