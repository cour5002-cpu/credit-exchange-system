from flask import Flask, jsonify, request

from app.config import config_by_name
from app.extensions import init_extensions
from app.models import (
    CreditExchangeApplication,
    CreditExchangeAllocation,
    CreditConversionRule,
    CreditExchangeRecord,
    Appeal,
    Complaint,
    ApplicationAdvisor,
    Attachment,
    CollegeTask,
    ExtensionRequest,
    HourAwardRecord,
    HourApplication,
    HourApplicationAttachment,
    HourApplicationMember,
    HourApplicationReview,
    OperationLog,
    Notification,
    ReviewAssignment,
    RuleFile,
    Student,
    StudentCreditRecord,
    StudentHourAccount,
    StudentHourTransaction,
    SystemConfig,
    TaskMember,
    TaskRegistration,
    TaskResultSubmission,
    TaskResultSubmissionVersion,
    TaskType,
    Teacher,
    User,
)
from app.modules.admin.routes import admin_bp
from app.modules.advisor.routes import advisor_bp
from app.modules.api import api_bp
from app.modules.auth.routes import auth_bp
from app.modules.credit_exchange.routes import credit_exchange_bp
from app.modules.main.routes import main_bp
from app.modules.reviewer.routes import reviewer_bp
from app.modules.student.routes import student_bp
from app.modules.teacher.routes import teacher_bp
from app.commands.seed_data import register_seed_commands


def create_app(config_name: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    if config_name == "production" and app.config["SECRET_KEY"] in {"dev-secret-key", "change-me", ""}:
        raise RuntimeError("生产环境必须通过 SECRET_KEY 配置强随机密钥")

    init_extensions(app)
    register_blueprints(app)
    register_error_handlers(app)
    register_seed_commands(app)

    return app


def register_blueprints(app: Flask) -> None:
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(advisor_bp)
    app.register_blueprint(reviewer_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(credit_exchange_bp)
    app.register_blueprint(api_bp)


def register_error_handlers(app: Flask) -> None:
    @app.errorhandler(403)
    def forbidden(error):
        if request.path.startswith("/api/v1/"):
            return jsonify({"code": 40301, "message": "无权限", "data": None}), 403
        return getattr(error, "description", "Forbidden"), 403

    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith("/api/v1/"):
            return jsonify({"code": 40401, "message": "资源不存在", "data": None}), 404
        return getattr(error, "description", "Not Found"), 404

    @app.errorhandler(413)
    def payload_too_large(error):
        if request.path.startswith("/api/v1/"):
            return jsonify({"code": 41301, "message": "上传文件超过 10MB 限制", "data": None}), 413
        return "上传文件超过 10MB 限制", 413
