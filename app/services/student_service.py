from flask_login import current_user

from app.models.student import Student


def get_current_student():
    return Student.query.filter_by(user_id=current_user.id).first()
