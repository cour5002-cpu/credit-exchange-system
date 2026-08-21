from flask import request
from flask_login import current_user, login_required

from app.core.responses import handle_business, ok
from app.modules.api.blueprint import api_bp
from app.services.student_admin_service import update_expected_graduation_date
from app.utils.permissions import role_required


@api_bp.route("/admin/students/<int:student_id>/expected-graduation-date", methods=["PATCH"])
@login_required
@role_required("admin")
def admin_update_expected_graduation_date(student_id):
    def action():
        student = update_expected_graduation_date(
            current_user, student_id, request.get_json(silent=True)
        )
        return ok({
            "student_id": student.id,
            "expected_graduation_date": (
                student.expected_graduation_date.isoformat()
                if student.expected_graduation_date else None
            ),
        })
    return handle_business(action)
