from flask_login import LoginManager
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "请先登录后再访问该页面。"


def init_extensions(app) -> None:
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
