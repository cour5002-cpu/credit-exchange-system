from app.extensions import db
from app.models.task_type import TaskType


def list_task_types(enabled=None):
    query = TaskType.query
    if enabled is True:
        query = query.filter_by(status="enabled")
    if enabled is False:
        query = query.filter(TaskType.status != "enabled")
    return query.order_by(TaskType.sort_order.asc(), TaskType.id.asc()).all()


def create_task_type(data):
    item = TaskType(
        type_code=data["type_code"],
        type_name=data["type_name"],
        sort_order=int(data.get("sort_order") or 0),
        status=data.get("status") or "enabled",
        allow_student_self=_as_bool(data.get("allow_student_self", True)),
        allow_admin_task=_as_bool(data.get("allow_admin_task", True)),
        allow_teacher_task=_as_bool(data.get("allow_teacher_task", True)),
    )
    db.session.add(item)
    db.session.commit()
    return item


def update_task_type(item, data):
    for field in ("type_code", "type_name", "status"):
        if field in data:
            setattr(item, field, data[field])
    if "sort_order" in data:
        item.sort_order = int(data.get("sort_order") or 0)
    for field in ("allow_student_self", "allow_admin_task", "allow_teacher_task"):
        if field in data:
            setattr(item, field, _as_bool(data[field]))
    db.session.commit()
    return item


def set_task_type_status(item, status):
    item.status = status
    db.session.commit()
    return item


def task_type_to_dict(item):
    return {
        "id": item.id,
        "type_code": item.type_code,
        "type_name": item.type_name,
        "status": item.status,
        "sort_order": item.sort_order,
        "allow_student_self": item.allow_student_self,
        "allow_admin_task": item.allow_admin_task,
        "allow_teacher_task": item.allow_teacher_task,
    }


def _as_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on", "是"}
    return bool(value)
