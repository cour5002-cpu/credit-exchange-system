from datetime import datetime
from zoneinfo import ZoneInfo


BUSINESS_TIMEZONE_NAME = "Asia/Shanghai"
BUSINESS_TIMEZONE = ZoneInfo(BUSINESS_TIMEZONE_NAME)


def business_now() -> datetime:
    """Return the current business time as a naive value for existing DATETIME columns."""
    return datetime.now(BUSINESS_TIMEZONE).replace(tzinfo=None)


def business_now_aware() -> datetime:
    return datetime.now(BUSINESS_TIMEZONE)


def parse_api_datetime(value) -> datetime | None:
    """Normalize ISO 8601 input to a naive Asia/Shanghai database value."""
    if not value:
        return None
    if isinstance(value, datetime):
        parsed = value
    else:
        text = str(value).strip()
        if text.endswith(("Z", "z")):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)

    if parsed.tzinfo is None:
        localized = parsed.replace(tzinfo=BUSINESS_TIMEZONE)
    else:
        localized = parsed.astimezone(BUSINESS_TIMEZONE)
    return localized.replace(tzinfo=None)


def format_api_datetime(value: datetime | None) -> str | None:
    """Serialize database or aware datetimes as ISO 8601 with an explicit +08:00 offset."""
    if value is None:
        return None
    if value.tzinfo is None:
        localized = value.replace(tzinfo=BUSINESS_TIMEZONE)
    else:
        localized = value.astimezone(BUSINESS_TIMEZONE)
    return localized.isoformat(timespec="seconds")


def system_time_payload() -> dict:
    now = business_now_aware()
    return {
        "server_time": now.isoformat(timespec="seconds"),
        "timezone": BUSINESS_TIMEZONE_NAME,
        "utc_offset": "+08:00",
    }
