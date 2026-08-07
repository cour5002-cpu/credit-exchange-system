from app.models.attachment import Attachment
from app.schemas.base import owner_attachments, student_summary, teacher_summary
from app.schemas.common import iso, number
from app.utils.time_utils import business_now


def task_created_payload(task):
    return {"id": task.id, "task_no": task.task_no, "status": task.status}


def task_registration_created_payload(registration):
    return {"registration_id": registration.id, "status": registration.status}


def task_summary(task):
    return {
        "id": task.id,
        "task_no": task.task_no,
        "title": task.title,
        "publisher_role": task.publisher_type,
        "publisher_name": task.publisher.real_name if task.publisher else None,
        "task_type_id": task.task_type_id,
        "task_type_name": task.task_type.type_name if task.task_type else None,
        "description": task.description,
        "requirement": task.requirement,
        "registration_deadline": iso(task.registration_deadline),
        "status": task.status,
        "advisor": teacher_summary(task.advisor) if task.advisor else None,
        "created_at": iso(task.created_at),
        "updated_at": iso(task.updated_at),
    }


def task_leader_payload(task, leader_student_id):
    return {
        "task_id": task.id,
        "leader_student_id": leader_student_id,
        "leader_assigned": True,
        "task_status": task.status,
    }


def student_team_payload(task, members, student):
    leader = next((item for item in members if item.is_leader), None)
    submission = task.result_submissions[0] if task.result_submissions else None
    return {
        "task": task_detail(task),
        "members": [task_member_summary(item) for item in members],
        "leader_student_id": leader.student_id if leader else None,
        "can_submit_result": bool(leader and leader.student_id == student.id and not submission),
        "can_resubmit_result": bool(
            leader
            and leader.student_id == student.id
            and submission
            and submission.status == "advisor_rejected"
            and task.status == "task_in_progress"
        ),
        "task_result_submission_id": submission.id if submission else None,
    }


def task_result_created_payload(submission):
    return {
        "submission_id": submission.id,
        "hour_application_id": submission.hour_application_id,
        "status": submission.hour_application.status if submission.hour_application else submission.status,
        "submission_status": submission.status,
    }


def task_result_summary(submission):
    latest_version = submission.versions[-1] if submission.versions else None
    current_attachment_ids = set(latest_version.attachment_ids or []) if latest_version else set()
    attachment_query = Attachment.query.filter_by(
        owner_type="task_result",
        owner_id=submission.id,
        status="active",
    )
    if current_attachment_ids:
        attachment_query = attachment_query.filter(Attachment.id.in_(current_attachment_ids))
    active_attachment_count = attachment_query.count()
    return {
        "id": submission.id,
        "task_id": submission.task_id,
        "task_no": submission.task.task_no,
        "task_title": submission.task.title,
        "leader": student_summary(submission.leader),
        "summary": submission.summary,
        "requested_hours": number(submission.requested_hours),
        "status": submission.status,
        "hour_application_id": submission.hour_application_id,
        "attachment_count": active_attachment_count,
        "submitted_at": iso(submission.created_at),
        "updated_at": iso(submission.updated_at),
    }


def task_result_detail_payload(submission):
    latest_version = submission.versions[-1] if submission.versions else None
    current_attachment_ids = set(latest_version.attachment_ids or []) if latest_version else set()
    return {
        "submission": {
            "id": submission.id,
            "task_id": submission.task_id,
            "leader_student_id": submission.leader_student_id,
            "summary": submission.summary,
            "requested_hours": number(submission.requested_hours),
            "status": submission.status,
            "hour_application_id": submission.hour_application_id,
            "advisor_comment": submission.advisor_comment,
            "created_at": iso(submission.created_at),
            "advisor_reviewed_at": iso(submission.advisor_reviewed_at),
        },
        "task": task_detail(submission.task),
        "attachments": [
            item for item in owner_attachments("task_result", submission.id)
            if not current_attachment_ids or item["id"] in current_attachment_ids
        ],
        "versions": [
            {
                "id": version.id,
                "version_no": version.version_no,
                "summary": version.summary,
                "requested_hours": number(version.requested_hours),
                "attachment_ids": version.attachment_ids or [],
                "submitted_by": version.submitted_by,
                "submitted_at": iso(version.created_at),
            }
            for version in submission.versions
        ],
    }


def task_detail_payload(task):
    return {
        "task": task_detail(task),
        "attachments": owner_attachments("college_task", task.id),
        "registrations": [
            task_registration_summary(item)
            for item in sorted(task.registrations, key=lambda item: (item.created_at, item.id))
        ],
        "members": [
            task_member_summary(item)
            for item in sorted(task.members, key=lambda item: (not item.is_leader, item.id))
            if item.status == "active"
        ],
    }


def student_task_detail_payload(task, registration):
    payload = task_detail_payload(task)
    payload["registration"] = task_registration_summary(registration) if registration else None
    payload["can_register"] = (
        task.status in {"published", "registration_open"}
        and registration is None
        and bool(task.registration_deadline and task.registration_deadline > business_now())
    )
    return payload


def task_detail(task):
    item = task_summary(task)
    members = [task_member_summary(member) for member in task.members if member.status == "active"]
    leader = next((member for member in members if member["is_leader"]), None)
    item.update({
        "major_name": task.major_name,
        "course_name": task.course_name,
        "registration_start_at": iso(task.registration_start_at),
        "published_at": iso(task.published_at),
        "admin_review_comment": task.admin_review_comment,
        "registrations": [task_registration_summary(item) for item in task.registrations],
        "members": members,
        "leader": leader["student"] if leader else None,
        "actions": {
            "can_register": task.status in {"published", "registration_open"}
            and bool(task.registration_deadline and task.registration_deadline > business_now()),
            "can_select": task.status == "selection_pending",
        },
    })
    return item


def task_registration_summary(registration):
    if not registration:
        return None
    return {
        "id": registration.id,
        "task_id": registration.task_id,
        "student": student_summary(registration.student) if registration.student else None,
        "student_id": registration.student_id,
        "status": registration.status,
        "reason": registration.apply_reason,
        "submitted_at": iso(registration.created_at),
        "selected_at": iso(registration.selected_at),
    }


def task_member_summary(member):
    return {
        "id": member.id,
        "task_id": member.task_id,
        "registration_id": member.registration_id,
        "student_id": member.student_id,
        "student_name": member.student.name if member.student else None,
        "student": student_summary(member.student) if member.student else None,
        "is_leader": bool(member.is_leader),
        "selected_at": iso(member.created_at),
    }
