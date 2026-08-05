import os

from flask import current_app, request, send_file
from flask_login import current_user, login_required

from app.core.responses import handle_business, ok
from app.modules.api.blueprint import api_bp
from app.modules.api.serializers import conversion_rule_summary, rule_file_summary
from app.services.week4_credit_exchange_service import (
    create_conversion_rule,
    create_rule_file,
    current_conversion_rule,
    get_rule_file,
    list_conversion_rules,
    list_rule_files,
    set_conversion_rule_status,
    update_conversion_rule,
)
from app.utils.permissions import role_required


@api_bp.route("/admin/rule-files", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_rule_file():
    data = request.get_json(silent=True) or {}
    return handle_business(lambda: ok(rule_file_summary(create_rule_file(current_user, data))))


@api_bp.route("/rule-files", methods=["GET"])
@login_required
def api_rule_files():
    keyword = (request.args.get("keyword") or "").strip() or None
    rule_type = (request.args.get("rule_type") or "").strip() or None
    usage_type = (request.args.get("usage_type") or "").strip() or None
    return handle_business(lambda: ok({"items": [rule_file_summary(item) for item in list_rule_files(keyword, rule_type, usage_type)]}))


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
    return handle_business(lambda: ok({"rule": conversion_rule_summary(create_conversion_rule(current_user, data))}))


@api_bp.route("/admin/credit-conversion-rules", methods=["GET"])
@login_required
@role_required("admin")
def admin_conversion_rules():
    status = (request.args.get("status") or "").strip() or None
    keyword = (request.args.get("keyword") or "").strip() or None
    return handle_business(lambda: ok({"items": [conversion_rule_summary(item) for item in list_conversion_rules(status, keyword)]}))


@api_bp.route("/credit-conversion-rules/current", methods=["GET"])
@login_required
def api_current_conversion_rule():
    return handle_business(lambda: ok({"rule": conversion_rule_summary(current_conversion_rule())}))


@api_bp.route("/admin/credit-conversion-rules/<int:rule_id>", methods=["PATCH"])
@login_required
@role_required("admin")
def admin_update_conversion_rule(rule_id):
    data = request.get_json(silent=True) or {}
    return handle_business(lambda: ok({"rule": conversion_rule_summary(update_conversion_rule(current_user, rule_id, data))}))


@api_bp.route("/admin/credit-conversion-rules/<int:rule_id>/enable", methods=["POST"])
@login_required
@role_required("admin")
def admin_enable_conversion_rule(rule_id):
    return handle_business(lambda: ok({"rule": conversion_rule_summary(set_conversion_rule_status(current_user, rule_id, "active"))}))


@api_bp.route("/admin/credit-conversion-rules/<int:rule_id>/disable", methods=["POST"])
@login_required
@role_required("admin")
def admin_disable_conversion_rule(rule_id):
    return handle_business(lambda: ok({"rule": conversion_rule_summary(set_conversion_rule_status(current_user, rule_id, "inactive"))}))
