from flask import request
from flask_login import current_user, login_required

from app.core.responses import handle_business as _handle_business, ok
from app.modules.api.blueprint import api_bp
from app.modules.api.route_helpers import paged_response as _paged_response
from app.schemas.credit_exchange import (
    credit_exchange_created_payload as _credit_exchange_created_payload,
    credit_exchange_detail_payload as _credit_exchange_detail_payload,
    credit_exchange_final_payload as _credit_exchange_final_payload,
    credit_exchange_form_payload as _credit_exchange_form_payload,
    credit_exchange_summary as _credit_exchange_summary,
    hour_award_summary as _hour_award_summary,
)
from app.schemas.hour_application import id_status_payload as _id_status_payload
from app.services.week4_credit_exchange_service import (
    admin_batch_final_approve_credit_exchanges,
    admin_final_approve_credit_exchange,
    admin_final_reject_credit_exchange,
    advisor_approve_credit_exchange,
    advisor_reject_credit_exchange,
    get_admin_credit_exchange,
    get_advisor_credit_exchange,
    get_exchange_form_data,
    get_student_credit_exchange,
    list_admin_pending_final_credit_exchanges,
    list_advisor_pending_credit_exchanges,
    list_available_hour_awards,
    list_student_credit_exchanges,
    submit_credit_exchange,
)
from app.utils.permissions import role_required


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
