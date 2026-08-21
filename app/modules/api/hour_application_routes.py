from flask import request
from flask_login import current_user, login_required

from app.core.responses import handle_business as _handle_business, ok
from app.modules.api.blueprint import api_bp
from app.modules.api.route_helpers import paged_response as _paged_response
from app.schemas.hour_application import (
    admin_detail_payload as _admin_detail_payload,
    admin_extension_detail_payload as _admin_extension_detail_payload,
    admin_hour_application_summary as _admin_hour_application_summary,
    advisor_detail_payload as _advisor_detail_payload,
    application_created_payload as _application_created_payload,
    assign_payload as _assign_payload,
    extension_created_payload as _extension_created_payload,
    extension_detail_payload as _extension_detail_payload,
    extension_eligibility_payload as _extension_eligibility_payload,
    extension_request_payload as _extension_request_payload,
    extension_review_payload as _extension_review_payload,
    final_approve_payload as _final_approve_payload,
    final_review_payload as _final_review_payload,
    hour_application_detail_payload as _hour_application_detail_payload,
    hour_application_summary as _hour_application_summary,
    id_status_payload as _id_status_payload,
    pending_final_summary as _pending_final_summary,
    reviewer_action_payload as _reviewer_action_payload,
    reviewer_detail_payload as _reviewer_detail_payload,
)
from app.services.extension_request_service import (
    create_extension_request,
    get_extension_eligibility,
    get_visible_extension_request,
    list_admin_extensions,
    list_advisor_pending_extensions,
    review_extension_request,
)
from app.services.week3_hour_application_service import (
    advisor_approve,
    advisor_reject,
    assign_reviewer,
    close_unfinishable_application,
    create_student_application,
    final_approve,
    final_reject,
    get_advisor_application,
    get_advisor_material_application,
    get_application,
    get_reviewer_application,
    get_visible_application_for_student,
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
from app.services.admin_batch_service import (
    batch_assign_hour_application_reviewer,
    batch_final_approve_hour_applications,
)
from app.utils.permissions import role_required


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


@api_bp.route("/student/hour-applications/<int:application_id>/extension-eligibility", methods=["GET"])
@login_required
@role_required("student")
def student_extension_eligibility(application_id):
    return _handle_business(lambda: ok(_extension_eligibility_payload(
        get_extension_eligibility(current_user, application_id)
    )))


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
    return _handle_business(lambda: ok(_advisor_detail_payload(get_advisor_material_application(current_user, application_id))))


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


@api_bp.route("/admin/extension-requests/<int:extension_request_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_extension_request_detail(extension_request_id):
    return _handle_business(lambda: ok(_admin_extension_detail_payload(get_visible_extension_request(current_user, extension_request_id))))


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


@api_bp.route("/admin/hour-applications/batch-assign-reviewer", methods=["POST"])
@login_required
@role_required("admin")
def admin_batch_assign_reviewer():
    return _handle_business(lambda: ok(batch_assign_hour_application_reviewer(
        current_user, request.get_json(silent=True)
    )))


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


@api_bp.route("/admin/hour-applications/batch-final-approve", methods=["POST"])
@login_required
@role_required("admin")
def admin_batch_final_approve():
    return _handle_business(lambda: ok(batch_final_approve_hour_applications(
        current_user, request.get_json(silent=True)
    )))


@api_bp.route("/admin/hour-applications/<int:application_id>/final-reject", methods=["POST"])
@login_required
@role_required("admin")
def admin_final_reject(application_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_id_status_payload(final_reject(current_user, application_id, data.get("comment")))))
