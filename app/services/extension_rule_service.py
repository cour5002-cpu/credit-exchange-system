from app.core.errors import BusinessError
from app.extensions import db
from app.models.extension_rule import ExtensionRule
from app.models.extension_rule_task_type import ExtensionRuleTaskType
from app.models.task_type import TaskType
from app.services.service_helpers import add_operation, parse_datetime
from app.utils.pagination import paginate_query
from app.utils.time_utils import business_now, format_api_datetime


RULE_STATUSES = {"enabled", "disabled"}
RULE_FIELDS = {
    "rule_name",
    "ordinary_max_days",
    "special_threshold_days",
    "special_max_days",
    "max_extension_requests",
    "default_material_due_days",
    "allow_beyond_graduation",
    "task_type_ids",
    "effective_at",
    "status",
}


def create_extension_rule(user, payload):
    payload = _object(payload, RULE_FIELDS, RULE_FIELDS)
    data, task_types = _validate_rule_payload(payload)
    _ensure_no_enabled_same_effective_conflict(
        data["effective_at"], {item.id for item in task_types}, data["status"]
    )
    rule = ExtensionRule(
        **data,
        version=1,
        created_by=user.id,
        updated_by=user.id,
    )
    db.session.add(rule)
    db.session.flush()
    _replace_task_types(rule, task_types)
    add_operation(user.id, "extension_rule", rule.id, "create", None, rule.status)
    db.session.commit()
    return rule


def list_extension_rules(status, effective, page, page_size):
    if status not in {"all", "enabled", "disabled"}:
        raise BusinessError("status 只能是 all、enabled 或 disabled")
    if effective not in {"all", "current", "future"}:
        raise BusinessError("effective 只能是 all、current 或 future")
    query = ExtensionRule.query
    if status != "all":
        query = query.filter_by(status=status)
    now = business_now()
    if effective == "current":
        query = query.filter(ExtensionRule.effective_at <= now)
    elif effective == "future":
        query = query.filter(ExtensionRule.effective_at > now)
    return paginate_query(
        query.order_by(ExtensionRule.effective_at.desc(), ExtensionRule.id.desc()),
        page,
        page_size,
    )


def get_extension_rule(rule_id):
    rule = db.session.get(ExtensionRule, rule_id)
    if not rule:
        raise BusinessError("延期规则不存在", code=40401, status=404)
    return rule


def update_extension_rule(user, rule_id, payload):
    payload = _object(payload, RULE_FIELDS | {"version"}, {"version"})
    rule = ExtensionRule.query.filter_by(id=rule_id).with_for_update().first()
    if not rule:
        raise BusinessError("延期规则不存在", code=40401, status=404)
    expected_version = _positive_int(payload["version"], "version")
    if rule.version != expected_version:
        raise BusinessError("延期规则已被其他管理员修改，请刷新后重试", code=40906, status=409)
    merged = {
        "rule_name": payload.get("rule_name", rule.rule_name),
        "ordinary_max_days": payload.get("ordinary_max_days", rule.ordinary_max_days),
        "special_threshold_days": payload.get("special_threshold_days", rule.special_threshold_days),
        "special_max_days": payload.get("special_max_days", rule.special_max_days),
        "max_extension_requests": payload.get("max_extension_requests", rule.max_extension_requests),
        "default_material_due_days": payload.get("default_material_due_days", rule.default_material_due_days),
        "allow_beyond_graduation": payload.get("allow_beyond_graduation", rule.allow_beyond_graduation),
        "task_type_ids": payload.get("task_type_ids", [item.id for item in rule.task_types]),
        "effective_at": payload.get("effective_at", rule.effective_at),
        "status": payload.get("status", rule.status),
    }
    data, task_types = _validate_rule_payload(merged)
    _ensure_no_enabled_same_effective_conflict(
        data["effective_at"], {item.id for item in task_types}, data["status"], rule.id
    )
    before = rule.status
    for key, value in data.items():
        setattr(rule, key, value)
    rule.version += 1
    rule.updated_by = user.id
    _replace_task_types(rule, task_types)
    add_operation(user.id, "extension_rule", rule.id, "update", before, rule.status)
    db.session.commit()
    return rule


def set_extension_rule_status(user, rule_id, status, payload):
    if status not in RULE_STATUSES:
        raise BusinessError("延期规则状态不合法")
    payload = _object(payload, {"version"}, {"version"})
    rule = ExtensionRule.query.filter_by(id=rule_id).with_for_update().first()
    if not rule:
        raise BusinessError("延期规则不存在", code=40401, status=404)
    expected_version = _positive_int(payload["version"], "version")
    if rule.version != expected_version:
        raise BusinessError("延期规则已被其他管理员修改，请刷新后重试", code=40906, status=409)
    if status == "enabled":
        _ensure_no_enabled_same_effective_conflict(
            rule.effective_at, {item.id for item in rule.task_types}, status, rule.id
        )
    before = rule.status
    if before != status:
        rule.status = status
        rule.version += 1
        rule.updated_by = user.id
        add_operation(user.id, "extension_rule", rule.id, status, before, status)
        db.session.commit()
    return rule


def current_extension_rule(task_type_id, at=None):
    try:
        task_type_id = int(task_type_id)
    except (TypeError, ValueError):
        raise BusinessError("task_type_id 必须是正整数")
    if task_type_id <= 0:
        raise BusinessError("task_type_id 必须是正整数")
    at = at or business_now()
    return (
        ExtensionRule.query.join(
            ExtensionRuleTaskType,
            ExtensionRuleTaskType.rule_id == ExtensionRule.id,
        )
        .filter(
            ExtensionRule.status == "enabled",
            ExtensionRule.effective_at <= at,
            ExtensionRuleTaskType.task_type_id == task_type_id,
        )
        .order_by(ExtensionRule.effective_at.desc(), ExtensionRule.id.desc())
        .first()
    )


def extension_rule_snapshot(rule, applied_at=None):
    applied_at = applied_at or business_now()
    return {
        "schema_version": 1,
        "rule_id": rule.id,
        "rule_name": rule.rule_name,
        "rule_version": rule.version,
        "ordinary_max_days": rule.ordinary_max_days,
        "special_threshold_days": rule.special_threshold_days,
        "special_max_days": rule.special_max_days,
        "max_extension_requests": rule.max_extension_requests,
        "default_material_due_days": rule.default_material_due_days,
        "allow_beyond_graduation": rule.allow_beyond_graduation,
        "task_type_ids": sorted(item.id for item in rule.task_types),
        "effective_at": format_api_datetime(rule.effective_at),
        "applied_at": format_api_datetime(applied_at),
    }


def ensure_default_extension_rule(user):
    existing = ExtensionRule.query.first()
    if existing:
        return existing
    task_types = TaskType.query.order_by(TaskType.sort_order, TaskType.id).all()
    if not task_types:
        return None
    rule = ExtensionRule(
        rule_name="V3迁移默认延期规则",
        ordinary_max_days=30,
        special_threshold_days=30,
        special_max_days=365,
        max_extension_requests=1,
        default_material_due_days=30,
        allow_beyond_graduation=True,
        effective_at=business_now(),
        status="enabled",
        version=1,
        created_by=user.id,
        updated_by=user.id,
    )
    db.session.add(rule)
    db.session.flush()
    _replace_task_types(rule, task_types)
    return rule


def _validate_rule_payload(payload):
    name = payload.get("rule_name")
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 128:
        raise BusinessError("rule_name 必须是 1 到 128 个字符")
    data = {
        "rule_name": name.strip(),
        "ordinary_max_days": _positive_int(payload.get("ordinary_max_days"), "ordinary_max_days"),
        "special_threshold_days": _positive_int(payload.get("special_threshold_days"), "special_threshold_days"),
        "special_max_days": _positive_int(payload.get("special_max_days"), "special_max_days"),
        "max_extension_requests": _positive_int(payload.get("max_extension_requests"), "max_extension_requests"),
        "default_material_due_days": _positive_int(payload.get("default_material_due_days"), "default_material_due_days"),
        "allow_beyond_graduation": _boolean(payload.get("allow_beyond_graduation"), "allow_beyond_graduation"),
        "effective_at": parse_datetime(payload.get("effective_at")),
        "status": payload.get("status"),
    }
    if data["status"] not in RULE_STATUSES:
        raise BusinessError("status 只能是 enabled 或 disabled")
    if data["ordinary_max_days"] > data["special_max_days"]:
        raise BusinessError("ordinary_max_days 不能大于 special_max_days")
    if data["special_threshold_days"] > data["special_max_days"]:
        raise BusinessError("special_threshold_days 不能大于 special_max_days")
    ids = _strict_ids(payload.get("task_type_ids"), "task_type_ids")
    task_types = TaskType.query.filter(TaskType.id.in_(ids)).all()
    if len(task_types) != len(ids):
        raise BusinessError("task_type_ids 包含不存在的任务类型", code=40401, status=404)
    return data, task_types


def _replace_task_types(rule, task_types):
    desired = {task_type.id: task_type for task_type in task_types}
    for link in list(rule.task_type_links):
        if link.task_type_id not in desired:
            rule.task_type_links.remove(link)
    existing_ids = {link.task_type_id for link in rule.task_type_links}
    for task_type_id, task_type in desired.items():
        if task_type_id not in existing_ids:
            rule.task_type_links.append(ExtensionRuleTaskType(task_type=task_type))
    db.session.flush()


def _ensure_no_enabled_same_effective_conflict(effective_at, task_type_ids, status, exclude_rule_id=None):
    if status != "enabled":
        return
    query = ExtensionRule.query.join(ExtensionRuleTaskType).filter(
        ExtensionRule.status == "enabled",
        ExtensionRule.effective_at == effective_at,
        ExtensionRuleTaskType.task_type_id.in_(task_type_ids),
    )
    if exclude_rule_id:
        query = query.filter(ExtensionRule.id != exclude_rule_id)
    if query.first():
        raise BusinessError("同一任务类型和生效时间不能存在多条启用规则", code=40902, status=409)


def _object(value, allowed, required):
    if not isinstance(value, dict):
        raise BusinessError("请求体必须是 JSON 对象")
    fields = set(value)
    if fields - allowed:
        raise BusinessError("请求包含未定义字段")
    if required - fields:
        raise BusinessError("请求缺少必填字段")
    return value


def _positive_int(value, field):
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise BusinessError(f"{field} 必须是正整数")
    return value


def _boolean(value, field):
    if not isinstance(value, bool):
        raise BusinessError(f"{field} 必须是布尔值")
    return value


def _strict_ids(value, field):
    if not isinstance(value, list) or not value:
        raise BusinessError(f"{field} 必须是非空数组")
    if any(isinstance(item, bool) or not isinstance(item, int) or item <= 0 for item in value):
        raise BusinessError(f"{field} 只能包含正整数")
    if len(set(value)) != len(value):
        raise BusinessError(f"{field} 不能包含重复 ID")
    return value
