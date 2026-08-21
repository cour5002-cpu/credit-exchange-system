from app.core.errors import BusinessError
from app.models.student import Student
from app.models.teacher import Teacher


def current_student(user):
    """Return the active student identity associated with a user."""

    student = Student.query.filter_by(user_id=user.id, status="active").first()
    if not student:
        raise BusinessError("当前账号没有可用学生身份", code=40301, status=403)
    return student


def current_teacher(user, required_flag=None):
    """Return the active teacher identity and optionally require a role flag."""

    teacher = Teacher.query.filter_by(user_id=user.id, status="active").first()
    if not teacher:
        raise BusinessError("当前账号没有可用教师身份", code=40301, status=403)
    if required_flag and required_flag not in teacher.role_flag_list:
        raise BusinessError("当前教师不具备该操作角色", code=40301, status=403)
    return teacher
