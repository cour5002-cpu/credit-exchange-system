from app.models.attachment import Attachment
from app.utils.time_utils import format_api_datetime


def student_summary(student):
    return {
        "id": student.id,
        "student_no": student.student_no,
        "name": student.name,
        "college": student.college,
        "major": student.major,
        "class_name": student.class_name,
        "grade": student.grade,
    }


def teacher_summary(teacher):
    return {
        "id": teacher.id,
        "username": teacher.user.username if teacher.user else None,
        "teacher_no": teacher.teacher_no,
        "name": teacher.name,
        "college": None,
        "major": teacher.major_name,
        "role_flags": teacher.role_flag_list,
    }


def attachment_summary(attachment):
    return {
        "id": attachment.id,
        "biz_type": attachment.biz_type,
        "file_name": attachment.file_name,
        "file_size": attachment.file_size,
        "mime_type": attachment.mime_type,
        "url": f"/api/v1/attachments/{attachment.id}",
        "uploaded_by": attachment.uploaded_by,
        "status": attachment.status,
        "voided_by": attachment.voided_by,
        "voided_at": format_api_datetime(attachment.voided_at),
        "void_reason": attachment.void_reason,
        "created_at": format_api_datetime(attachment.created_at),
    }


def owner_attachments(owner_type, owner_id):
    return [
        attachment_summary(item)
        for item in Attachment.query.filter_by(
            owner_type=owner_type,
            owner_id=owner_id,
            status="active",
        ).order_by(Attachment.id.asc()).all()
    ]


def operation_record_summary(record):
    return {
        "id": record.id,
        "module": record.module,
        "biz_type": record.biz_type,
        "biz_id": record.biz_id,
        "action": record.action,
        "detail": record.detail,
        "created_at": format_api_datetime(record.created_at),
    }
