import re

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app import create_app
from app.config import TestingConfig
from app.extensions import db


def create_isolated_test_app():
    _ensure_test_database()
    app = create_app("testing")
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app


def _ensure_test_database():
    url = make_url(TestingConfig.SQLALCHEMY_DATABASE_URI)
    if not url.drivername.startswith("mysql"):
        return
    database_name = url.database or ""
    if not re.fullmatch(r"[A-Za-z0-9_]+", database_name):
        raise RuntimeError("测试数据库名称只能包含字母、数字和下划线")
    server_url = url.set(database="mysql")
    engine = create_engine(server_url, isolation_level="AUTOCOMMIT")
    try:
        with engine.connect() as connection:
            connection.execute(text(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            ))
    finally:
        engine.dispose()
