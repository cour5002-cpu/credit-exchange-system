from flask import flash, jsonify, redirect, request, url_for
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import event


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "请先登录后再访问该页面。"


@login_manager.unauthorized_handler
def unauthorized():
    if request.path.startswith("/api/v1/"):
        return jsonify({"code": 40101, "message": "未登录或登录过期", "data": None}), 401
    flash(login_manager.login_message, "warning")
    return redirect(url_for(login_manager.login_view))


def init_extensions(app) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    with app.app_context():
        engine = db.engine
        if engine.dialect.name == "mysql":
            @event.listens_for(engine, "connect")
            def set_mysql_session_timezone(dbapi_connection, _connection_record):
                cursor = dbapi_connection.cursor()
                try:
                    cursor.execute("SET time_zone = '+08:00'")
                finally:
                    cursor.close()
