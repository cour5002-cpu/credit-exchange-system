from datetime import datetime
from random import randint


def generate_application_no(prefix: str) -> str:
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}{now}{randint(100, 999)}"
