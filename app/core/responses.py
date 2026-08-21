from flask import jsonify

from app.core.errors import BusinessError


def ok(data=None):
    """Return the established successful API response envelope."""

    return jsonify({"code": 0, "message": "success", "data": data or {}})


def fail(message, code=40001, status=400):
    """Return the established failed API response envelope."""

    return jsonify({"code": code, "message": message, "data": None}), status


def handle_business(func):
    """Translate expected business and validation errors to API responses."""

    try:
        return func()
    except BusinessError as exc:
        return fail(str(exc), code=exc.code, status=exc.status)
    except ValueError as exc:
        return fail(str(exc))
