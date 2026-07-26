import os

from dotenv import load_dotenv
from sqlalchemy.engine import make_url


load_dotenv(override=True)


class BaseConfig:
    BUSINESS_TIMEZONE = "Asia/Shanghai"
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///dev.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
    UPLOAD_FOLDER = os.path.join(os.getcwd(), "app", "static", "uploads")


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_SAMESITE = "Lax"


def _testing_database_uri():
    configured = os.getenv("TEST_DATABASE_URL")
    if configured:
        return configured
    url = make_url(BaseConfig.SQLALCHEMY_DATABASE_URI)
    if url.drivername.startswith("mysql") and url.database:
        return url.set(database=f"{url.database}_test").render_as_string(hide_password=False)
    return "sqlite:///test.db"


class TestingConfig(BaseConfig):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = _testing_database_uri()


config_by_name = {
    "default": DevelopmentConfig,
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}
