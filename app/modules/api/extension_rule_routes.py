from flask import request
from flask_login import current_user, login_required

from app.core.responses import handle_business, ok
from app.core.validation import parse_pagination_args
from app.modules.api.blueprint import api_bp
from app.schemas.extension_rule import extension_rule_summary, public_extension_rule
from app.services.extension_rule_service import (
    create_extension_rule,
    current_extension_rule,
    get_extension_rule,
    list_extension_rules,
    set_extension_rule_status,
    update_extension_rule,
)
from app.utils.permissions import role_required


@api_bp.route("/admin/extension-rules", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_extension_rule():
    return handle_business(lambda: ok({
        "rule": extension_rule_summary(create_extension_rule(current_user, request.get_json(silent=True)))
    }))


@api_bp.route("/admin/extension-rules", methods=["GET"])
@login_required
@role_required("admin")
def admin_extension_rules():
    def action():
        page, page_size = parse_pagination_args(
            request.args.get("page", 1), request.args.get("page_size", 20)
        )
        result = list_extension_rules(
            (request.args.get("status") or "all").strip(),
            (request.args.get("effective") or "all").strip(),
            page,
            page_size,
        )
        return ok({
            "items": [extension_rule_summary(item) for item in result.items],
            "page": result.page,
            "page_size": result.page_size,
            "total": result.total,
            "pages": result.pages,
        })
    return handle_business(action)


@api_bp.route("/admin/extension-rules/<int:rule_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_extension_rule_detail(rule_id):
    return handle_business(lambda: ok({"rule": extension_rule_summary(get_extension_rule(rule_id))}))


@api_bp.route("/admin/extension-rules/<int:rule_id>", methods=["PATCH"])
@login_required
@role_required("admin")
def admin_update_extension_rule(rule_id):
    return handle_business(lambda: ok({
        "rule": extension_rule_summary(
            update_extension_rule(current_user, rule_id, request.get_json(silent=True))
        )
    }))


@api_bp.route("/admin/extension-rules/<int:rule_id>/enable", methods=["POST"])
@login_required
@role_required("admin")
def admin_enable_extension_rule(rule_id):
    return handle_business(lambda: ok({
        "rule": extension_rule_summary(set_extension_rule_status(
            current_user, rule_id, "enabled", request.get_json(silent=True)
        ))
    }))


@api_bp.route("/admin/extension-rules/<int:rule_id>/disable", methods=["POST"])
@login_required
@role_required("admin")
def admin_disable_extension_rule(rule_id):
    return handle_business(lambda: ok({
        "rule": extension_rule_summary(set_extension_rule_status(
            current_user, rule_id, "disabled", request.get_json(silent=True)
        ))
    }))


@api_bp.route("/extension-rules/current", methods=["GET"])
@login_required
def current_extension_rule_api():
    return handle_business(lambda: ok({
        "rule": public_extension_rule(current_extension_rule(request.args.get("task_type_id")))
    }))
