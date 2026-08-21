from app.core.errors import BusinessError
from app.extensions import db
from app.models.attachment import Attachment
from app.models.operation_log import OperationLog
from app.utils.time_utils import parse_api_datetime


def bind_attachments(
    owner_type,
    owner_id,
    attachment_ids,
    user_id,
    expected_biz_type=None,
):
    ids = normalize_id_list(attachment_ids)
    if not ids:
        return
    expected_biz_type = expected_biz_type or owner_type
    attachments = Attachment.query.filter(
        Attachment.id.in_(ids),
        Attachment.status == "active",
    ).all()
    if len(attachments) != len(set(ids)):
        raise BusinessError("附件不存在或无权使用", code=40301, status=403)
    for attachment in attachments:
        if attachment.uploaded_by != user_id or attachment.biz_type != expected_biz_type:
            raise BusinessError("附件不存在或无权使用", code=40301, status=403)
        if attachment.owner_id and attachment.owner_id != owner_id:
            raise BusinessError("附件已绑定其他业务", code=40902, status=409)
        attachment.owner_type = owner_type
        attachment.owner_id = owner_id


def add_operation(user_id, biz_type, biz_id, action, before_status, after_status):
    db.session.add(OperationLog(
        user_id=user_id,
        module="week5",
        biz_type=biz_type,
        biz_id=biz_id,
        action=action,
        detail=f"{before_status}->{after_status}",
    ))


def require_status(actual, expected):
    if actual != expected:
        raise BusinessError("当前状态不允许执行该操作", code=40901, status=409)


def required_str(payload, *keys):
    for key in keys:
        value = (payload.get(key) or "").strip()
        if value:
            return value
    raise BusinessError(f"{keys[0]} 不能为空")


def required_int(payload, key):
    value = payload.get(key)
    try:
        value = int(value)
    except (TypeError, ValueError):
        raise BusinessError(f"{key} 必须是整数")
    if value <= 0:
        raise BusinessError(f"{key} 必须大于 0")
    return value


def required_choice(value, choices, message):
    value = (value or "").strip()
    if value not in choices:
        raise BusinessError(message)
    return value


def normalize_id_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        value = [item.strip() for item in value.split(",") if item.strip()]
    if not isinstance(value, (list, tuple, set)):
        raise BusinessError("ID 列表格式不正确")
    ids = []
    for item in value:
        try:
            item_id = int(item)
        except (TypeError, ValueError):
            raise BusinessError("ID 列表只能包含整数")
        if item_id <= 0:
            raise BusinessError("ID 列表只能包含正整数")
        if item_id not in ids:
            ids.append(item_id)
    return ids


def parse_datetime(value):
    try:
        return parse_api_datetime(value)
    except (TypeError, ValueError):
        raise BusinessError("时间格式必须是 ISO 8601 字符串")
