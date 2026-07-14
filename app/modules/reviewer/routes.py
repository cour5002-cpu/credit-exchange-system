from flask import Blueprint, jsonify
from flask_login import login_required

from app.utils.permissions import role_required


reviewer_bp = Blueprint("reviewer", __name__, url_prefix="/reviewer")


@reviewer_bp.route("/dashboard")
@login_required
@role_required("reviewer")
def dashboard():
    return jsonify(
        {
            "code": 0,
            "message": "success",
            "data": {
                "role": "reviewer",
                "endpoint": "reviewer.dashboard",
            },
        }
    )
