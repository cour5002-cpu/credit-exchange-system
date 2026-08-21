from flask import Blueprint, jsonify
from flask_login import login_required

from app.utils.permissions import role_required


advisor_bp = Blueprint("advisor", __name__, url_prefix="/advisor")


@advisor_bp.route("/dashboard")
@login_required
@role_required("advisor")
def dashboard():
    return jsonify(
        {
            "code": 0,
            "message": "success",
            "data": {
                "role": "advisor",
                "endpoint": "advisor.dashboard",
            },
        }
    )
