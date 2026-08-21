from decimal import Decimal

from app.utils.time_utils import format_api_datetime


def number(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def iso(value):
    return format_api_datetime(value)
