from flask import request
from flask_login import current_user, login_required

from app.core.responses import handle_business as _handle_business, ok
from app.modules.api.blueprint import api_bp
from app.modules.api.payloads import _complaint_detail_payload, _complaint_summary, _paged_response
from app.services.week5_appeal_task_service import create_complaint, get_complaint, list_complaints
from app.utils.permissions import role_required


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
