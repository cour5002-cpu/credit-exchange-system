from flask import request
from flask_login import current_user, login_required, login_user, logout_user

from app.core.responses import fail, ok
from app.extensions import db
from app.models.student import Student
from app.models.teacher import Teacher
from app.modules.api.blueprint import api_bp
from app.modules.api.serializers import student_summary, teacher_summary
from app.services.auth_service import authenticate_user


@api_bp.route("/auth/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    remember = bool(data.get("remember"))
    if not username or not password:
        return fail("账号和密码不能为空")

    user = authenticate_user(username, password)
    if not user:
        return fail("账号或密码错误，或账号已被禁用", code=40101, status=401)

    login_user(user, remember=remember)
    user.last_login_at = db.func.now()
    db.session.commit()
    return ok(_current_user_payload())


@api_bp.route("/auth/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return ok()


@api_bp.route("/me")
@login_required
def me():
    return ok(_current_user_payload())


def _current_user_payload():
    student = Student.query.filter_by(user_id=current_user.id).first()
    teacher = Teacher.query.filter_by(user_id=current_user.id).first()
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.effective_role,
        "roles": current_user.roles,
        "student": student_summary(student) if student else None,
        "teacher": teacher_summary(teacher) if teacher else None,
    }
