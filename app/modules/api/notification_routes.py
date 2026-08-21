from flask import request
from flask_login import current_user, login_required

from app.core.errors import BusinessError
from app.core.responses import handle_business, ok
from app.core.validation import parse_pagination_args
from app.modules.api.blueprint import api_bp
from app.schemas.notification import announcement_payload, notification_detail, notification_list_item
from app.services.announcement_service import (
    get_announcement_batch, list_announcement_batches, publish_announcement,
    replace_announcement, stop_announcement,
)
from app.services.notification_service import (
    business_available, get_owned_notification, list_notifications, mark_all_read,
    mark_read, mark_selected_read, unread_summary,
)
from app.utils.permissions import role_required
from app.utils.time_utils import format_api_datetime


def _strict_query(allowed):
    unknown = set(request.args) - set(allowed)
    if unknown:
        raise BusinessError(f"包含未定义查询参数: {', '.join(sorted(unknown))}")


def _json_object(required_fields):
    data = request.get_json(silent=True)
    if not isinstance(data, dict) or set(data) != set(required_fields):
        raise BusinessError("请求体字段不完整或包含未定义字段")
    return data


@api_bp.route("/notifications", methods=["GET"])
@login_required
def notification_list():
    def action():
        _strict_query({"page", "page_size", "status", "academic_year", "semester"})
        page, page_size = parse_pagination_args(request.args.get("page", 1), request.args.get("page_size", 20))
        result, period, periods = list_notifications(
            current_user.id, request.args.get("status", "all"), request.args.get("academic_year"),
            request.args.get("semester"), page, page_size,
        )
        return ok({"items": [notification_list_item(x) for x in result.items], "page": result.page,
                   "page_size": result.page_size, "total": result.total, "pages": result.pages,
                   "selected_period": {"academic_year": period[0], "semester": period[1]},
                   "available_periods": periods})
    return handle_business(action)


@api_bp.route("/notifications/unread-count", methods=["GET"])
@login_required
def notification_unread_count():
    return handle_business(lambda: (_strict_query({"academic_year", "semester"}), ok(unread_summary(
        current_user.id, request.args.get("academic_year"), request.args.get("semester")
    )))[1])


@api_bp.route("/notifications/<int:notification_id>", methods=["GET"])
@login_required
def notification_get(notification_id):
    def action():
        _strict_query(set())
        item = get_owned_notification(current_user.id, notification_id)
        return ok(notification_detail(item, business_available(item, current_user)))
    return handle_business(action)


@api_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def notification_read(notification_id):
    def action():
        if request.data:
            raise BusinessError("该接口不接受请求体")
        item = mark_read(current_user.id, notification_id)
        return ok({"id": item.id, "is_read": True, "read_at": format_api_datetime(item.read_at)})
    return handle_business(action)


@api_bp.route("/notifications/read", methods=["POST"])
@login_required
def notification_read_selected():
    return handle_business(lambda: ok(mark_selected_read(current_user.id, _json_object({"ids"})["ids"])))


@api_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def notification_read_all():
    def action():
        data = _json_object({"up_to_id", "academic_year", "semester"})
        return ok(mark_all_read(current_user.id, data["up_to_id"], data["academic_year"], data["semester"]))
    return handle_business(action)


@api_bp.route("/admin/notifications/announcements", methods=["POST"])
@login_required
@role_required("admin")
def announcement_publish():
    def action():
        item, count = publish_announcement(current_user, request.get_json(silent=True))
        from app.extensions import db
        db.session.commit()
        return ok({"batch_key": item.announcement_batch_key, "announcement_status": "active",
                   "recipient_count": count, "published_at": format_api_datetime(item.created_at),
                   "expires_at": format_api_datetime(item.expires_at)})
    return handle_business(action)


@api_bp.route("/admin/notifications/announcements", methods=["GET"])
@login_required
@role_required("admin")
def announcement_list():
    def action():
        _strict_query({"page", "page_size"})
        page, page_size = parse_pagination_args(request.args.get("page", 1), request.args.get("page_size", 20))
        result = list_announcement_batches(page, page_size)
        return ok({"items": [announcement_payload(item, count) for item, count in result.items],
                   "page": result.page, "page_size": result.page_size, "total": result.total, "pages": result.pages})
    return handle_business(action)


@api_bp.route("/admin/notifications/announcements/<batch_key>", methods=["GET"])
@login_required
@role_required("admin")
def announcement_get(batch_key):
    return handle_business(lambda: ok(announcement_payload(*get_announcement_batch(batch_key), detail=True)))


@api_bp.route("/admin/notifications/announcements/<batch_key>/stop", methods=["POST"])
@login_required
@role_required("admin")
def announcement_stop(batch_key):
    def action():
        if request.data:
            raise BusinessError("该接口不接受请求体")
        item = stop_announcement(current_user, batch_key)
        return ok({"batch_key": batch_key, "announcement_status": "stopped", "stopped_at": format_api_datetime(item.stopped_at)})
    return handle_business(action)


@api_bp.route("/admin/notifications/announcements/<batch_key>/replace", methods=["POST"])
@login_required
@role_required("admin")
def announcement_replace(batch_key):
    def action():
        old, new, count = replace_announcement(current_user, batch_key, request.get_json(silent=True))
        return ok({"old_batch_key": old.announcement_batch_key, "old_status": "stopped",
                   "new_batch_key": new.announcement_batch_key, "new_status": "active", "recipient_count": count})
    return handle_business(action)
