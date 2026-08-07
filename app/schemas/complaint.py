from app.schemas.base import owner_attachments
from app.schemas.common import iso


def complaint_summary(complaint):
    # V1 对管理员保持匿名：响应中不返回提交账号或学生信息。
    return {
        "id": complaint.id,
        "content": complaint.content,
        "status": complaint.status,
        "created_at": iso(complaint.created_at),
        "viewed_at": iso(complaint.viewed_at),
    }


def complaint_detail_payload(complaint):
    return {
        "complaint": complaint_summary(complaint),
        "attachments": owner_attachments("complaint", complaint.id),
    }
