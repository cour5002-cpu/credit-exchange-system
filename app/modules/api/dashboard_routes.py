from flask import make_response
from flask_login import login_required

from app.core.responses import handle_business, ok
from app.modules.api.blueprint import api_bp
from app.schemas.admin_dashboard import admin_dashboard_payload
from app.services.admin_dashboard_service import get_admin_dashboard_sections
from app.utils.permissions import role_required


@api_bp.route("/admin/dashboard", methods=["GET"])
@login_required
@role_required("admin")
def admin_dashboard_api():
    def payload():
        response = make_response(ok(admin_dashboard_payload(get_admin_dashboard_sections())))
        response.headers["Cache-Control"] = "no-store"
        return response

    return handle_business(payload)
