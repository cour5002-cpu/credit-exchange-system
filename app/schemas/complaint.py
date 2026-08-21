from app.models.student import Student
from app.schemas.base import owner_attachments
from app.schemas.common import iso


def complaint_created_payload(complaint):
    return {
        "id": complaint.id,
        "complaint_no": complaint.complaint_no,
        "category": complaint.category,
        "status": complaint.status,
        "created_at": iso(complaint.created_at),
    }


def student_complaint_summary(complaint):
    return {
        "id": complaint.id,
        "complaint_no": complaint.complaint_no,
        "category": complaint.category,
        "content_preview": complaint.content[:80],
        "status": complaint.status,
        "handling_result": complaint.handling_result,
        "created_at": iso(complaint.created_at),
        "handled_at": iso(complaint.handled_at),
    }


def student_complaint_detail_payload(complaint):
    return {
        "complaint": {
            "id": complaint.id,
            "complaint_no": complaint.complaint_no,
            "category": complaint.category,
            "content": complaint.content,
            "status": complaint.status,
            "handling_result": complaint.handling_result,
            "handling_opinion": complaint.handling_opinion,
            "created_at": iso(complaint.created_at),
            "handled_at": iso(complaint.handled_at),
        },
        "attachments": owner_attachments("complaint", complaint.id),
    }


def admin_complaint_summary(complaint):
    student = Student.query.filter_by(user_id=complaint.submitter_user_id).first()
    return {
        "id": complaint.id,
        "complaint_no": complaint.complaint_no,
        "category": complaint.category,
        "content_preview": complaint.content[:80],
        "submitter": _submitter(complaint, student),
        "status": complaint.status,
        "handling_result": complaint.handling_result,
        "created_at": iso(complaint.created_at),
        "viewed_at": iso(complaint.viewed_at),
        "processing_started_at": iso(complaint.processing_started_at),
        "handled_at": iso(complaint.handled_at),
    }


def admin_complaint_detail_payload(complaint):
    data = admin_complaint_summary(complaint)
    data.update({
        "content": complaint.content,
        "handling_opinion": complaint.handling_opinion,
        "handled_by": {
            "user_id": complaint.handled_by,
            "real_name": complaint.handler.real_name if complaint.handler else None,
        } if complaint.handled_by else None,
        "updated_at": iso(complaint.updated_at),
    })
    return {
        "complaint": data,
        "attachments": owner_attachments("complaint", complaint.id),
    }


def complaint_processing_payload(complaint):
    return {
        "id": complaint.id,
        "status": complaint.status,
        "processing_started_at": iso(complaint.processing_started_at),
    }


def complaint_resolved_payload(complaint):
    return {
        "id": complaint.id,
        "status": complaint.status,
        "handling_result": complaint.handling_result,
        "handling_opinion": complaint.handling_opinion,
        "handled_at": iso(complaint.handled_at),
    }


# Compatibility exports for callers that still import the old names.
complaint_summary = admin_complaint_summary
complaint_detail_payload = admin_complaint_detail_payload


def _submitter(complaint, student):
    return {
        "user_id": complaint.submitter_user_id,
        "student_id": student.id if student else None,
        "student_no": student.student_no if student else None,
        "name": student.name if student else (complaint.submitter.real_name if complaint.submitter else None),
    }
