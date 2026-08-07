from app.extensions import db
from app.models.attachment import Attachment
from app.models.task_result_submission import TaskResultSubmission
from app.schemas.base import (
    attachment_summary,
    owner_attachments,
    student_summary,
    teacher_summary,
)
from app.schemas.common import iso, number
from app.services.week3_hour_application_service import latest_reviewer_result


def application_created_payload(application):
    return {
        "id": application.id,
        "application_no": application.application_no,
        "status": application.status,
    }


def extension_created_payload(extension):
    application = extension.application
    applicant = application.applicant or application.student
    return {
        "extension_request_id": extension.id,
        "applicant": student_summary(applicant),
        "applicant_name": applicant.name,
        "status": extension.status,
        "application_status": application.status,
        "extension_days": extension.extension_days,
        "review_level": extension.review_level,
    }


def extension_review_payload(extension, result_status):
    return {"id": extension.id, "status": result_status}


def id_status_payload(application):
    return {"id": application.id, "status": application.status}


def assign_payload(application):
    return {
        "id": application.id,
        "status": application.status,
        "reviewer_teacher_id": application.assigned_teacher_id,
    }


def reviewer_action_payload(application, review_result):
    return {"id": application.id, "status": application.status, "review_result": review_result}


def final_approve_payload(application, award):
    return {
        "id": application.id,
        "status": application.status,
        "hour_award_record_id": award.id,
    }


def hour_application_summary(application):
    applicant = application.applicant or application.student
    primary_advisor = next(
        (link for link in application.advisor_links if link.advisor_role == "primary"),
        None,
    )
    return {
        "id": application.id,
        "application_no": application.application_no,
        "title": application.title,
        "application_type": application.application_type,
        "source_type": application.source_type,
        "task_type_id": application.task_type_id,
        "task_type_name": application.task_type_name,
        "applicant": student_summary(applicant) if applicant else None,
        "applicant_name": applicant.name if applicant else None,
        "leader": student_summary(application.leader) if application.leader else None,
        "advisor_teacher_id": primary_advisor.teacher_id if primary_advisor else None,
        "requested_hours": number(application.requested_hours),
        "reviewer_suggested_hours": number(application.reviewer_suggested_hours),
        "final_hours": number(application.final_hours),
        "status": application.status,
        "submitted_at": iso(application.submitted_at),
        "created_at": iso(application.created_at),
        "updated_at": iso(application.updated_at),
    }


def extension_request_payload(extension):
    application = extension.application
    applicant = application.applicant or application.student
    return {
        "id": extension.id,
        "application_id": application.id,
        "applicant": student_summary(applicant),
        "applicant_name": applicant.name,
        "old_due_at": iso(extension.old_due_at),
        "requested_due_at": iso(extension.requested_due_at),
        "extension_days": extension.extension_days,
        "reason": extension.reason,
        "review_level": extension.review_level,
        "status": extension.status,
        "review_comment": extension.review_comment,
        "created_at": iso(extension.created_at),
        "reviewed_at": iso(extension.reviewed_at),
    }


def extension_detail_payload(extension):
    return {
        "extension_request": extension_request_payload(extension),
        "application": hour_application_summary(extension.application),
        "attachments": owner_attachments("extension_request", extension.id),
    }


def admin_hour_application_summary(application):
    item = hour_application_summary(application)
    item["can_operate"] = application.status in {"pending_assignment", "pending_admin_final"}
    return item


def pending_final_summary(application):
    item = hour_application_summary(application)
    result = latest_reviewer_result(application.id)
    item["review_result"] = review_record(result)["decision"] if result else None
    return item


def hour_application_detail_payload(application):
    workflow_progress = hour_application_workflow_progress(application)
    return {
        "id": application.id,
        "application_no": application.application_no,
        "status": application.status,
        "application": hour_application_detail(application),
        "applicant": student_summary(application.applicant or application.student),
        "members": application_members(application),
        "advisors": application_advisors(application),
        "attachments": application_attachments(application),
        "reviews": application_reviews(application),
        "advisor_reviewed_at": iso(application.advisor_reviewed_at),
        "assigned_at": workflow_progress["admin_assignment"]["completed_at"],
        "reviewer_reviewed_at": iso(application.reviewer_reviewed_at),
        "final_reviewed_at": iso(application.final_reviewed_at),
        "workflow_progress": workflow_progress,
        "actions": action_flags(application),
    }


def admin_extension_detail_payload(extension):
    application = extension.application
    student = application.applicant or application.student
    return {
        "extension_request_id": extension.id,
        "hour_application_id": application.id,
        "old_due_at": iso(extension.old_due_at),
        "requested_due_at": iso(extension.requested_due_at),
        "extension_days": extension.extension_days,
        "review_level": extension.review_level,
        "status": extension.status,
        "reason": extension.reason,
        "student": {
            "id": student.id,
            "student_no": student.student_no,
            "name": student.name,
        },
        "attachments": [
            {
                "id": item.id,
                "filename": item.file_name,
                "url": f"/api/v1/attachments/{item.id}",
            }
            for item in Attachment.query.filter_by(
                owner_type="extension_request",
                owner_id=extension.id,
                status="active",
            ).order_by(Attachment.id.asc()).all()
        ],
    }


def advisor_detail_payload(application):
    payload = hour_application_detail_payload(application)
    payload["can_operate"] = application.status in {"submitted", "material_submitted"}
    return payload


def admin_detail_payload(application):
    payload = hour_application_detail_payload(application)
    payload["assignments"] = review_assignments(application)
    return payload


def reviewer_detail_payload(application):
    payload = hour_application_detail_payload(application)
    payload["requested_hours"] = number(application.requested_hours)
    payload["can_review"] = application.status == "pending_review"
    return payload


def final_review_payload(application):
    payload = hour_application_detail_payload(application)
    result = latest_reviewer_result(application.id)
    payload["reviewer_result"] = review_record(result) if result else None
    payload["final_hours"] = number(
        application.final_hours or application.reviewer_suggested_hours
    )
    return payload


def hour_application_detail(application):
    item = hour_application_summary(application)
    workflow_progress = hour_application_workflow_progress(application)
    item.update({
        "description": application.description,
        "achievement_summary": application.achievement_summary or application.achievement_submission,
        "major_name": application.major_name,
        "course_name": application.course_name,
        "material_due_at": iso(application.material_due_at),
        "extension_count": application.extension_count,
        "source_task_id": application.source_task_id,
        "task_result_submission_id": application.task_result_submission_id,
        "assigned_reviewer": teacher_summary(application.assigned_teacher)
        if application.assigned_teacher else None,
        "appeal_advice": application.appeal_advice,
        "members": application_members(application),
        "advisors": application_advisors(application),
        "attachments": application_attachments(application),
        "reviews": application_reviews(application),
        "assignments": review_assignments(application),
        "advisor_reviewed_at": iso(application.advisor_reviewed_at),
        "assigned_at": workflow_progress["admin_assignment"]["completed_at"],
        "reviewer_reviewed_at": iso(application.reviewer_reviewed_at),
        "final_reviewed_at": iso(application.final_reviewed_at),
        "workflow_progress": workflow_progress,
        "actions": action_flags(application),
    })
    return item


def hour_application_workflow_progress(application):
    assignments = sorted(
        getattr(application, "review_assignments", []),
        key=lambda item: (item.assigned_at, item.id),
    )
    latest_assignment = assignments[-1] if assignments else None
    return {
        "student_submission": {
            "completed": bool(application.submitted_at),
            "completed_at": iso(application.submitted_at),
        },
        "advisor_confirmation": {
            "completed": bool(application.advisor_reviewed_at),
            "completed_at": iso(application.advisor_reviewed_at),
        },
        "admin_assignment": {
            "completed": latest_assignment is not None,
            "completed_at": iso(latest_assignment.assigned_at) if latest_assignment else None,
        },
        "reviewer_review": {
            "completed": bool(application.reviewer_reviewed_at),
            "completed_at": iso(application.reviewer_reviewed_at),
        },
        "admin_final_confirmation": {
            "completed": bool(application.final_reviewed_at),
            "completed_at": iso(application.final_reviewed_at),
        },
    }


def application_members(application):
    links = sorted(application.member_links, key=lambda item: (not item.is_leader, item.id))
    return [
        {
            "student": student_summary(link.student),
            "is_leader": bool(link.is_leader),
            "can_view": bool(link.can_view),
            "joined_at": iso(link.joined_at),
        }
        for link in links
        if link.status == "active"
    ]


def application_advisors(application):
    links = sorted(
        application.advisor_links,
        key=lambda item: (item.advisor_role != "primary", item.id),
    )
    return [
        {
            "teacher": teacher_summary(link.teacher),
            "advisor_role": link.advisor_role,
            "can_operate": bool(link.can_operate),
            "reviewed_at": iso(link.reviewed_at),
        }
        for link in links
    ]


def application_attachments(application):
    generic_items = Attachment.query.filter_by(
        owner_type="hour_application",
        owner_id=application.id,
        status="active",
    ).order_by(Attachment.id.asc()).all()
    summaries = [attachment_summary(item) for item in generic_items]
    if application.application_type == "task_result" and application.task_result_submission_id:
        submission = db.session.get(TaskResultSubmission, application.task_result_submission_id)
        latest_version = submission.versions[-1] if submission and submission.versions else None
        current_attachment_ids = set(latest_version.attachment_ids or []) if latest_version else set()
        task_result_query = Attachment.query.filter_by(
            owner_type="task_result",
            owner_id=application.task_result_submission_id,
            status="active",
        )
        if current_attachment_ids:
            task_result_query = task_result_query.filter(Attachment.id.in_(current_attachment_ids))
        task_result_items = task_result_query.order_by(Attachment.id.asc()).all()
        summaries.extend(attachment_summary(item) for item in task_result_items)
    legacy_summaries = [
        {
            "id": item.id,
            "biz_type": "hour_application",
            "file_name": item.file_name,
            "file_size": item.file_size,
            "mime_type": item.file_type,
            "url": f"/static/{item.static_relative_path}",
            "uploaded_by": item.uploaded_by,
            "created_at": iso(item.created_at),
        }
        for item in getattr(application, "attachments", [])
    ]
    return summaries + legacy_summaries


def application_reviews(application):
    reviews = sorted(
        getattr(application, "reviews", []),
        key=lambda item: (item.created_at, item.id),
    )
    return [review_record(item) for item in reviews]


def review_record(review):
    if not review:
        return None
    return {
        "id": review.id,
        "stage": review.stage or "reviewer",
        "operator_role": review.operator_role or review.stage or "reviewer",
        "operator_name": None,
        "decision": review.decision or review.action,
        "before_status": review.before_status,
        "after_status": review.after_status,
        "requested_hours_snapshot": number(review.requested_hours_snapshot),
        "approved_hours": number(review.approved_hours),
        "comment": review.comment,
        "created_at": iso(review.created_at),
    }


def review_assignments(application):
    assignments = sorted(
        getattr(application, "review_assignments", []),
        key=lambda item: (item.assigned_at, item.id),
    )
    return [
        {
            "id": item.id,
            "reviewer": teacher_summary(item.reviewer),
            "assigned_by_name": None,
            "assign_type": "assign" if item.status == "active" else "reassign",
            "reason": item.assign_reason,
            "created_at": iso(item.assigned_at),
        }
        for item in assignments
    ]


def action_flags(application):
    return {
        "can_edit": application.status in {"draft", "advisor_rejected", "reviewer_rejected"},
        "can_submit": application.status in {"draft", "advisor_rejected", "reviewer_rejected"},
        "can_approve": application.status in {
            "submitted", "material_submitted", "pending_review", "pending_admin_final"
        },
        "can_reject": application.status in {
            "submitted", "material_submitted", "pending_review", "pending_admin_final"
        },
        "can_assign": application.status == "pending_assignment",
        "can_appeal": application.status in {
            "reviewer_modified_approved", "reviewer_rejected", "final_rejected"
        },
        "can_download": True,
    }
