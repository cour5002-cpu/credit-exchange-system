import re


MAINLAND_MOBILE_PATTERN = r"^1[3-9]\d{9}$"
_MAINLAND_MOBILE_RE = re.compile(MAINLAND_MOBILE_PATTERN)


def is_mainland_mobile(value):
    return isinstance(value, str) and bool(_MAINLAND_MOBILE_RE.fullmatch(value.strip()))

