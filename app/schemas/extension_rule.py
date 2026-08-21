from app.schemas.common import iso


def extension_rule_summary(rule):
    return {
        "id": rule.id,
        "rule_name": rule.rule_name,
        "ordinary_max_days": rule.ordinary_max_days,
        "special_threshold_days": rule.special_threshold_days,
        "special_max_days": rule.special_max_days,
        "max_extension_requests": rule.max_extension_requests,
        "default_material_due_days": rule.default_material_due_days,
        "allow_beyond_graduation": rule.allow_beyond_graduation,
        "effective_at": iso(rule.effective_at),
        "status": rule.status,
        "version": rule.version,
        "task_types": [
            {
                "id": item.id,
                "type_code": item.type_code,
                "type_name": item.type_name,
                "status": item.status,
            }
            for item in sorted(rule.task_types, key=lambda value: (value.sort_order, value.id))
        ],
        "created_at": iso(rule.created_at),
        "updated_at": iso(rule.updated_at),
    }


def public_extension_rule(rule):
    if not rule:
        return None
    return {
        "id": rule.id,
        "rule_name": rule.rule_name,
        "ordinary_max_days": rule.ordinary_max_days,
        "special_threshold_days": rule.special_threshold_days,
        "special_max_days": rule.special_max_days,
        "max_extension_requests": rule.max_extension_requests,
        "default_material_due_days": rule.default_material_due_days,
        "allow_beyond_graduation": rule.allow_beyond_graduation,
        "effective_at": iso(rule.effective_at),
        "version": rule.version,
    }
