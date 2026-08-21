from sqlalchemy.orm import relationship

from app.extensions import db


class Teacher(db.Model):
    __tablename__ = "teachers"

    id = db.Column(db.BigInteger, primary_key=True)
    user_id = db.Column(db.BigInteger, db.ForeignKey("users.id"), nullable=False)
    teacher_no = db.Column(db.String(64), unique=True, nullable=False)
    name = db.Column(db.String(64), nullable=False)
    major_name = db.Column(db.String(128))
    course_name = db.Column(db.String(128))
    department = db.Column(db.String(128))
    title = db.Column(db.String(64))
    role_flags = db.Column(db.String(128), nullable=False, default="advisor,reviewer")
    status = db.Column(db.String(20), nullable=False, default="active")
    created_at = db.Column(db.DateTime, server_default=db.func.now(), nullable=False)
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )

    user = relationship("User", lazy="joined")

    @property
    def role_flag_list(self):
        if not self.role_flags:
            return []
        return [
            item.strip()
            for item in self.role_flags.split(",")
            if item.strip() in {"advisor", "reviewer"}
        ]
