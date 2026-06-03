from flask_login import current_user

from app.models.teacher import Teacher


def get_current_teacher():
    return Teacher.query.filter_by(user_id=current_user.id).first()
