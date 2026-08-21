from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import IntegrityError

from app.core.errors import BusinessError
from app.extensions import db
from app.models.appeal import Appeal
from app.models.hour_application import HourApplication
from app.services.appeal_service import assign_reopened_appeal, get_admin_appeal
from app.services.appeal_workflow import require_hour_application_workflow
from app.services.college_task_service import admin_approve_task_publish
from app.services.week3_hour_application_service import assign_reviewer, final_approve
from app.services.week4_credit_exchange_service import admin_final_approve_credit_exchange


MAX_BATCH_SIZE = 100
MAX_COMMENT_LENGTH = 2000
MAX_FINAL_HOURS = Decimal("99999999.99")


def batch_final_approve_hour_applications(user, payload):
    payload = _object(payload, {"items", "comment"}, {"items"})
    comment = _comment(payload.get("comment"))
    items = _hour_final_items(payload["items"], "application_id")

    def action(item):
        application_id = item["id"]
        require_hour_application_workflow(application_id)
        application, award = final_approve(user, application_id, item["final_hours"], comment)
        return application.status, {"hour_award_record_id": award.id}

    return _run(items, action)


def batch_final_approve_credit_exchanges(user, payload):
    payload = _object(payload, {"exchange_ids", "ids", "comment"}, set())
    has_exchange_ids = "exchange_ids" in payload
    has_legacy_ids = "ids" in payload
    if has_exchange_ids == has_legacy_ids:
        raise BusinessError("必须且只能提供 exchange_ids")
    ids = _strict_ids(payload.get("exchange_ids") if has_exchange_ids else payload.get("ids"), "exchange_ids")
    comment = _comment(payload.get("comment"))
    items = [{"id": item_id} for item_id in ids]

    def action(item):
        application, record = admin_final_approve_credit_exchange(user, item["id"], comment)
        return application.status, {"credit_exchange_record_id": record.id}

    return _run(items, action)


def batch_final_approve_reopened_appeals(user, payload):
    payload = _object(payload, {"items", "comment"}, {"items"})
    comment = _comment(payload.get("comment"))
    items = _hour_final_items(payload["items"], "appeal_id")

    def action(item):
        appeal = get_admin_appeal(item["id"])
        if (appeal.target_type != "hour_application" or appeal.status != "processing"
                or appeal.reopen_stage != "pending_admin_final"):
            raise BusinessError("当前申诉不在复审最终确认环节", code=40901, status=409)
        target = db.session.get(HourApplication, appeal.target_id)
        if not target or target.status != "pending_admin_final":
            raise BusinessError("申诉关联课时申请不在最终确认状态", code=40901, status=409)
        application, award = final_approve(user, target.id, item["final_hours"], comment)
        return application.status, {
            "target_id": application.id,
            "target_status": application.status,
            "appeal_status": appeal.status,
            "hour_award_record_id": award.id,
        }

    return _run(items, action)


def batch_assign_hour_application_reviewer(user, payload):
    payload = _object(
        payload,
        {"application_ids", "reviewer_teacher_id", "comment"},
        {"application_ids", "reviewer_teacher_id"},
    )
    ids = _strict_ids(payload["application_ids"], "application_ids")
    reviewer_teacher_id = _positive_int(payload["reviewer_teacher_id"], "reviewer_teacher_id")
    comment = _comment(payload.get("comment"))
    items = [{"id": item_id} for item_id in ids]

    def action(item):
        application = assign_reviewer(user, item["id"], reviewer_teacher_id, comment)
        return application.status, {"reviewer_teacher_id": application.assigned_teacher_id}

    return _run(items, action)


def batch_assign_reopened_appeal_reviewer(user, payload):
    payload = _object(
        payload,
        {"appeal_ids", "reviewer_teacher_id", "comment"},
        {"appeal_ids", "reviewer_teacher_id"},
    )
    ids = _strict_ids(payload["appeal_ids"], "appeal_ids")
    reviewer_teacher_id = _positive_int(payload["reviewer_teacher_id"], "reviewer_teacher_id")
    comment = _comment(payload.get("comment"))
    items = [{"id": item_id} for item_id in ids]

    def action(item):
        appeal, target = assign_reopened_appeal(user, item["id"], reviewer_teacher_id, comment)
        return appeal.reopen_stage, {
            "target_id": target.id,
            "target_status": target.status,
            "reviewer_teacher_id": target.assigned_teacher_id,
        }

    return _run(items, action)


def batch_approve_task_publish_requests(user, payload):
    payload = _object(payload, {"task_ids", "comment"}, {"task_ids"})
    ids = _strict_ids(payload["task_ids"], "task_ids")
    comment = _comment(payload.get("comment"))
    items = [{"id": item_id} for item_id in ids]

    def action(item):
        task = admin_approve_task_publish(user, item["id"], comment)
        return task.status, {}

    return _run(items, action)


def _run(items, action):
    results = []
    for item in items:
        item_id = item["id"]
        try:
            status, extra = action(item)
            results.append(_result(item_id, True, status, None, None, extra))
        except BusinessError as exc:
            db.session.rollback()
            results.append(_result(item_id, False, None, exc.code, str(exc), {}))
        except IntegrityError:
            db.session.rollback()
            results.append(_result(item_id, False, None, 40902, "数据已被处理或违反唯一约束", {}))
    return {
        "requested_count": len(items),
        "success_count": sum(1 for item in results if item["success"]),
        "failed_count": sum(1 for item in results if not item["success"]),
        "items": results,
    }


def _result(item_id, success, status, error_code, error_message, extra):
    return {
        "id": item_id,
        "success": success,
        "status": status,
        "error_code": error_code,
        "error_message": error_message,
        **extra,
    }


def _hour_final_items(value, id_key):
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_BATCH_SIZE:
        raise BusinessError(f"items 必须是包含 1 到 {MAX_BATCH_SIZE} 项的数组")
    items = []
    seen = set()
    for raw in value:
        raw = _object(raw, {id_key, "final_hours"}, {id_key, "final_hours"})
        item_id = _positive_int(raw[id_key], id_key)
        if item_id in seen:
            raise BusinessError(f"{id_key} 不能重复")
        seen.add(item_id)
        items.append({"id": item_id, "final_hours": _final_hours(raw["final_hours"])})
    return items


def _strict_ids(value, field_name):
    if not isinstance(value, list) or not 1 <= len(value) <= MAX_BATCH_SIZE:
        raise BusinessError(f"{field_name} 必须是包含 1 到 {MAX_BATCH_SIZE} 项的数组")
    ids = []
    for raw in value:
        item_id = _positive_int(raw, field_name)
        if item_id in ids:
            raise BusinessError(f"{field_name} 不能包含重复 ID")
        ids.append(item_id)
    return ids


def _positive_int(value, field_name):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BusinessError(f"{field_name} 必须是正整数")
    return value


def _final_hours(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise BusinessError("final_hours 必须是数字或 null")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        raise BusinessError("final_hours 必须是数字或 null")
    if not number.is_finite() or number <= 0 or number > MAX_FINAL_HOURS:
        raise BusinessError("final_hours 必须大于 0 且不超过 99999999.99")
    if number.as_tuple().exponent < -2:
        raise BusinessError("final_hours 最多保留 2 位小数")
    return number


def _comment(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise BusinessError("comment 必须是字符串或 null")
    value = value.strip()
    if len(value) > MAX_COMMENT_LENGTH:
        raise BusinessError(f"comment 长度不能超过 {MAX_COMMENT_LENGTH} 个字符")
    return value or None


def _object(value, allowed_fields, required_fields):
    if not isinstance(value, dict):
        raise BusinessError("请求体必须是 JSON 对象")
    fields = set(value)
    if fields - allowed_fields:
        raise BusinessError("请求包含未定义字段")
    if required_fields - fields:
        raise BusinessError("请求缺少必填字段")
    return value
