from flask import Flask

from app.config import config_by_name
from app.extensions import init_extensions
from app.models import (
    CreditExchangeApplication,
    CreditExchangeRecord,
    HourApplication,
    HourApplicationAttachment,
    HourApplicationReview,
    OperationLog,
    Student,
    StudentHourAccount,
    StudentHourTransaction,
    SystemConfig,
    TaskType,
    Teacher,
    User,
)
from app.modules.admin.routes import admin_bp
from app.modules.auth.routes import auth_bp
from app.modules.credit_exchange.routes import credit_exchange_bp
from app.modules.main.routes import main_bp
from app.modules.student.routes import student_bp
from app.modules.teacher.routes import teacher_bp
from app.commands.seed_data import register_seed_commands


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    init_extensions(app)
    register_blueprints(app)
    register_seed_commands(app)

    return app


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(credit_exchange_bp)
