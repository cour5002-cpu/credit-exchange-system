from flask import request
from flask_login import current_user, login_required

from app.core.responses import handle_business as _handle_business, ok
from app.modules.api.blueprint import api_bp
from app.modules.api.payloads import (
    _appeal_created_payload,
    _appeal_detail_payload,
    _appeal_review_payload,
    _appeal_summary,
    _credit_exchange_summary,
    _hour_application_summary,
    _paged_response,
    _reopened_appeal_payload,
)
from app.services.week5_appeal_task_service import (
    admin_approve_appeal,
    admin_reject_appeal,
    advisor_reconfirm_appeal,
    assign_reopened_appeal,
    create_appeal,
    get_admin_appeal,
    get_appealable_target,
    get_reviewer_appeal,
    get_student_appeal,
    list_admin_appeals,
    list_reopened_pending_advisor,
    list_reopened_pending_assignment,
    list_reviewer_appeals,
    list_student_appeals,
    review_reopened_appeal,
)
from app.utils.permissions import role_required


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
