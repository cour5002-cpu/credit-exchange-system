from app.utils.time_utils import business_now, format_api_datetime


WITHDRAWN_CONTENT = "该公告已撤回"


def announcement_status(item):
    if item.withdrawn_at:
        return "withdrawn"
    if item.stopped_at:
        return "stopped"
    if item.expires_at and item.expires_at <= business_now():
        return "expired"
    return "active"


def notification_list_item(item):
    return {
        "id": item.id,
        "category": item.category,
        "message_type": item.message_type,
        "title": item.title,
        "content_preview": (WITHDRAWN_CONTENT if item.withdrawn_at else item.content)[:80],
        "biz_type": item.biz_type,
        "biz_id": item.biz_id,
        "academic_year": item.academic_year,
        "semester": item.semester,
        "announcement_status": announcement_status(item) if item.announcement_batch_key else None,
        "is_read": item.read_at is not None,
        "read_at": format_api_datetime(item.read_at),
        "created_at": format_api_datetime(item.created_at),
    }


def notification_detail(item, biz_available):
    data = notification_list_item(item)
    data.pop("content_preview")
    data.update({
        "content": WITHDRAWN_CONTENT if item.withdrawn_at else item.content,
        "biz_available": biz_available,
        "expires_at": format_api_datetime(item.expires_at),
    })
    return data


def announcement_payload(item, recipient_count, detail=False):
    data = {
        "batch_key": item.announcement_batch_key,
        "title": item.title,
        "audience_roles": item.announcement_audience.split(",") if item.announcement_audience else [],
        "recipient_count": recipient_count,
        "announcement_status": announcement_status(item),
        "published_by": {
            "user_id": item.actor_user_id,
            "real_name": item.actor.real_name if item.actor else "系统",
        },
        "published_at": format_api_datetime(item.created_at),
        "expires_at": format_api_datetime(item.expires_at),
        "stopped_at": format_api_datetime(item.stopped_at),
        "withdrawn_at": format_api_datetime(item.withdrawn_at),
        "replaced_by_batch_key": item.replaced_by_batch_key,
    }
    if detail:
        data["content"] = WITHDRAWN_CONTENT if item.withdrawn_at else item.content
    return data
