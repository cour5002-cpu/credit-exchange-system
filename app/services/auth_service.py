from app.models.user import User


def authenticate_user(username: str, password: str):
    user = User.query.filter_by(username=username).first()
    if not user:
        return None
    if not user.check_password(password):
        return None
    if user.status != "active":
        return None
    return user


def get_home_endpoint_by_role(role: str) -> str:
    mapping = {
        "student": "student.dashboard",
        "teacher": "teacher.dashboard",
        "admin": "admin.dashboard",
    }
    return mapping.get(role, "main.index")
