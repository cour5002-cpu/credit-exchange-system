from flask_login import UserMixin
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db, login_manager


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.BigInteger, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    real_name = db.Column(db.String(64), nullable=False)
    phone = db.Column(db.String(32))
    email = db.Column(db.String(128))
    status = db.Column(db.String(20), nullable=False, default="active")
    last_login_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def is_active(self):
        return self.status == "active"

    @property
    def roles(self):
        role_set = {self.role}
        if self.role in {"advisor", "reviewer"}:
            role_set.add("teacher")

        try:
            from app.models.teacher import Teacher

            teacher = Teacher.query.filter_by(user_id=self.id).first()
            if teacher:
                role_set.update(teacher.role_flag_list)
                if teacher.role_flag_list:
                    role_set.add("teacher")
        except SQLAlchemyError:
            pass

        return sorted(role_set)

    def has_role(self, *roles: str) -> bool:
        return bool(set(roles) & set(self.roles))

    @property
    def effective_role(self) -> str:
        if self.role != "teacher":
            return self.role
        if "advisor" in self.roles:
            return "advisor"
        if "reviewer" in self.roles:
            return "reviewer"
        return self.role


@login_manager.user_loader
def load_user(user_id: str):
    return db.session.get(User, int(user_id))
