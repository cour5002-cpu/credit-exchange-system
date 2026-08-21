from app.utils.time_utils import business_now
from random import randint


def generate_application_no(prefix: str) -> str:
    now = business_now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{now}{randint(100, 999)}"
