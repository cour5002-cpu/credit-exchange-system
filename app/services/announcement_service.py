import re
import uuid

from app.core.errors import BusinessError
from app.extensions import db
from app.models.notification import Notification
from app.models.operation_log import OperationLog
from app.models.user import User
from app.schemas.notification import announcement_status
from app.services.notification_service import create_notification, current_period
from app.utils.pagination import PageResult
from app.utils.time_utils import business_now, parse_api_datetime


ROLE_ORDER = ("student", "advisor", "reviewer", "admin")
BATCH_RE = re.compile(r"^ann_[0-9a-f]{32}$")


def validate_batch_key(batch_key):
    if not BATCH_RE.fullmatch(str(batch_key or "")):
        raise BusinessError("公告批次键格式不正确")
    return batch_key


def _validate_payload(payload):
    if not isinstance(payload, dict):
        raise BusinessError("请求体必须是 JSON 对象")
    allowed = {"request_id", "title", "content", "audience_roles", "expires_at"}
    if set(payload) != allowed:
        raise BusinessError("公告请求字段不完整或包含未定义字段")
    request_id = payload.get("request_id")
    try:
        parsed_uuid = uuid.UUID(str(request_id), version=4)
    except (ValueError, AttributeError, TypeError):
        raise BusinessError("request_id 必须是 UUID v4")
    if str(parsed_uuid) != request_id:
        raise BusinessError("request_id 必须是小写标准 UUID v4")
    title = payload.get("title")
    content = payload.get("content")
    if not isinstance(title, str) or not 1 <= len(title.strip()) <= 200:
        raise BusinessError("title 长度必须为 1 到 200 个字符")
    if not isinstance(content, str) or not 1 <= len(content.strip()) <= 5000:
        raise BusinessError("content 长度必须为 1 到 5000 个字符")
    roles = payload.get("audience_roles")
    if not isinstance(roles, list) or not 1 <= len(roles) <= 4 or len(set(roles)) != len(roles):
        raise BusinessError("audience_roles 必须是 1 到 4 个不重复角色")
    if any(not isinstance(role, str) or role not in ROLE_ORDER for role in roles):
        raise BusinessError("audience_roles 包含不支持的角色")
    roles = [role for role in ROLE_ORDER if role in roles]
    expires_at = payload.get("expires_at")
    if expires_at is not None:
        if not isinstance(expires_at, str) or not re.search(r"(Z|[+-]\d\d:\d\d)$", expires_at, re.I):
            raise BusinessError("expires_at 必须是带时区的 ISO 8601 时间")
        try:
            expires_at = parse_api_datetime(expires_at)
        except (TypeError, ValueError):
            raise BusinessError("expires_at 格式不正确")
        if expires_at <= business_now():
            raise BusinessError("expires_at 必须晚于当前时间")
    batch_key = "ann_" + parsed_uuid.hex
    fingerprint = {
        "title": title.strip(), "content": content.strip(),
        "audience_roles": roles,
        "expires_at": expires_at.isoformat() if expires_at else None,
    }
    return batch_key, title.strip(), content.strip(), roles, expires_at, fingerprint


def _batch_first(batch_key):
    return Notification.query.filter_by(announcement_batch_key=batch_key).order_by(Notification.id).first()


def _recipient_users(roles):
    users = User.query.filter_by(status="active").order_by(User.id).all()
    return [user for user in users if any(user.has_role(role) for role in roles)]


def publish_announcement(user, payload, replaced_from=None):
    batch_key, title, content, roles, expires_at, fingerprint = _validate_payload(payload)
    existing = _batch_first(batch_key)
    if existing:
        saved = (existing.payload or {}).get("request_fingerprint")
        saved_from = (existing.payload or {}).get("replaced_from")
        if saved != fingerprint or saved_from != replaced_from:
            raise BusinessError("request_id 已用于其他公告内容", code=40902, status=409)
        return existing, Notification.query.filter_by(announcement_batch_key=batch_key).count()
    recipients = _recipient_users(roles)
    if not recipients:
        raise BusinessError("目标角色中没有正常收件账号", code=40901, status=409)
    academic_year, semester = current_period()
    audience = ",".join(roles)
    for recipient in recipients:
        create_notification(
            recipient.id, user.id, "announcement", "system_announcement", title, content,
            payload={"request_fingerprint": fingerprint, "replaced_from": replaced_from},
            dedupe_key=f"announcement:{batch_key}",
            academic_year=academic_year, semester=semester,
            announcement_batch_key=batch_key, announcement_audience=audience,
            expires_at=expires_at,
        )
    db.session.add(OperationLog(
        user_id=user.id, module="notification", biz_type="announcement", biz_id=None,
        action="replace" if replaced_from else "publish", detail=batch_key,
    ))
    db.session.flush()
    return _batch_first(batch_key), len(recipients)


def list_announcement_batches(page, page_size):
    rows = db.session.query(
        Notification.announcement_batch_key,
        db.func.min(Notification.id).label("first_id"),
        db.func.count(Notification.id).label("recipient_count"),
        db.func.min(Notification.created_at).label("published_at"),
    ).filter(Notification.announcement_batch_key.isnot(None)).group_by(
        Notification.announcement_batch_key
    ).order_by(db.func.min(Notification.created_at).desc(), Notification.announcement_batch_key.desc())
    total = rows.count()
    selected = rows.offset((page - 1) * page_size).limit(page_size).all()
    items = [(db.session.get(Notification, row.first_id), row.recipient_count) for row in selected]
    return PageResult(items=items, page=page, page_size=page_size, total=total,
                      pages=(total + page_size - 1) // page_size if total else 0)


def get_announcement_batch(batch_key):
    validate_batch_key(batch_key)
    item = _batch_first(batch_key)
    if not item:
        raise BusinessError("公告批次不存在", code=40401, status=404)
    return item, Notification.query.filter_by(announcement_batch_key=batch_key).count()


def stop_announcement(user, batch_key):
    item, _ = get_announcement_batch(batch_key)
    if item.stopped_at:
        return item
    if item.withdrawn_at or (item.expires_at and item.expires_at <= business_now()):
        raise BusinessError("当前公告状态不允许停止", code=40901, status=409)
    now = business_now()
    Notification.query.filter_by(announcement_batch_key=batch_key).update(
        {Notification.stopped_at: now}, synchronize_session=False
    )
    db.session.add(OperationLog(
        user_id=user.id, module="notification", biz_type="announcement", biz_id=None,
        action="stop", detail=batch_key,
    ))
    db.session.commit()
    return _batch_first(batch_key)


def replace_announcement(user, old_batch_key, payload):
    old, _ = get_announcement_batch(old_batch_key)
    batch_key, _, _, _, _, _ = _validate_payload(payload)
    existing = _batch_first(batch_key)
    if existing:
        new, count = publish_announcement(user, payload, replaced_from=old_batch_key)
        if old.replaced_by_batch_key != batch_key:
            raise BusinessError("request_id 已用于其他公告替换", code=40902, status=409)
        return old, new, count
    if announcement_status(old) != "active":
        raise BusinessError("旧公告不是 active 状态", code=40901, status=409)
    new, count = publish_announcement(user, payload, replaced_from=old_batch_key)
    now = business_now()
    Notification.query.filter_by(announcement_batch_key=old_batch_key).update({
        Notification.stopped_at: now,
        Notification.replaced_by_batch_key: new.announcement_batch_key,
    }, synchronize_session=False)
    db.session.commit()
    return _batch_first(old_batch_key), new, count
