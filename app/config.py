import os

from dotenv import load_dotenv


load_dotenv(override=True)


class BaseConfig:
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


config_by_name = {
    "default": DevelopmentConfig,
    "development": DevelopmentConfig,
    "production": ProductionConfig,
}
