from app.extensions import db


class SystemConfig(db.Model):
    __tablename__ = "system_configs"

    id = db.Column(db.BigInteger, primary_key=True)
    config_key = db.Column(db.String(128), unique=True, nullable=False)
    config_value = db.Column(db.String(500), nullable=False)
    description = db.Column(db.String(255))
    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.now(),
        onupdate=db.func.now(),
        nullable=False,
    )
