from decimal import Decimal, ROUND_DOWN

from app.models.system_config import SystemConfig


def get_config_value(key: str, default=None):
    item = SystemConfig.query.filter_by(config_key=key).first()
    if not item:
        return default
    return item.config_value


def get_credit_exchange_ratio():
    raw = get_config_value("credit_exchange_ratio", "10:1")
    hours_str, credits_str = raw.split(":")
    return Decimal(hours_str), Decimal(credits_str)


def calculate_credits_from_hours(hours):
    ratio_hours, ratio_credits = get_credit_exchange_ratio()
    result = (Decimal(str(hours)) / ratio_hours) * ratio_credits
    return result.quantize(Decimal("0.01"), rounding=ROUND_DOWN)
