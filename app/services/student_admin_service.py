from datetime import date

from app.core.errors import BusinessError
from app.extensions import db
from app.models.student import Student
from app.services.service_helpers import add_operation


def update_expected_graduation_date(user, student_id, payload):
    if not isinstance(payload, dict):
        raise BusinessError("请求体必须是 JSON 对象")
    if set(payload) != {"expected_graduation_date"}:
        raise BusinessError("请求只能包含 expected_graduation_date")
    student = db.session.get(Student, student_id)
    if not student:
        raise BusinessError("学生不存在", code=40401, status=404)
    value = payload["expected_graduation_date"]
    if value is None:
        parsed = None
    elif not isinstance(value, str):
        raise BusinessError("expected_graduation_date 必须是 YYYY-MM-DD 或 null")
    else:
        try:
            parsed = date.fromisoformat(value.strip())
        except ValueError:
            raise BusinessError("expected_graduation_date 必须是 YYYY-MM-DD 或 null")
    before = student.expected_graduation_date.isoformat() if student.expected_graduation_date else None
    student.expected_graduation_date = parsed
    add_operation(
        user.id,
        "student",
        student.id,
        "update_expected_graduation_date",
        before,
        parsed.isoformat() if parsed else None,
    )
    db.session.commit()
    return student
