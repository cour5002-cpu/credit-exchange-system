from datetime import datetime
from decimal import Decimal

from flask import request
from flask_login import current_user, login_required

from app.core.identity import current_teacher
from app.core.responses import fail, handle_business as _handle_business, ok
from app.core.validation import parse_pagination_args
from app.extensions import db
from app.models.attachment import Attachment
from app.models.appeal import Appeal
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.college_task import CollegeTask
from app.models.complaint import Complaint
from app.models.hour_application import HourApplication
from app.models.operation_log import OperationLog
from app.models.task_result_submission import TaskResultSubmission
from app.modules.api.blueprint import api_bp
from app.modules.api.serializers import (
    attachment_summary as _attachment_summary,
    conversion_rule_summary as _conversion_rule_summary,
    operation_record_summary as _operation_record_summary,
    owner_attachments as _owner_attachments,
    rule_file_summary as _rule_file_summary,
    student_summary as _student_summary,
    teacher_summary as _teacher_summary,
)
from app.services.week3_hour_application_service import (
    latest_reviewer_result,
)
from app.services.week4_credit_exchange_service import (
    get_admin_credit_exchange,
)
from app.services.week5_appeal_task_service import (
    create_complaint,
    get_complaint,
    list_complaints,
)
from app.utils.permissions import role_required
from app.utils.time_utils import business_now, format_api_datetime, parse_api_datetime


@api_bp.route("/student/complaints", methods=["POST"])
@login_required
@role_required("student")
def student_create_complaint():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_complaint_summary(create_complaint(current_user, data))))


@api_bp.route("/admin/complaints", methods=["GET"])
@login_required
@role_required("admin")
def admin_complaints():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_complaints(status, page, page_size),
        _complaint_summary,
    ))


@api_bp.route("/admin/complaints/<int:complaint_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_complaint_detail(complaint_id):
    return _handle_business(lambda: ok(_complaint_detail_payload(get_complaint(complaint_id, mark_viewed=True))))


@api_bp.route("/operation-records", methods=["GET"])
@login_required
@role_required("advisor", "reviewer", "admin")
def operation_records():
    role_scope = (request.args.get("role_scope") or "").strip()
    if role_scope not in {"advisor", "reviewer", "admin"} or not current_user.has_role(role_scope):
        return fail("role_scope 与当前用户角色不匹配", code=40301, status=403)
    query = OperationLog.query.filter_by(user_id=current_user.id)
    biz_type = (request.args.get("biz_type") or "").strip()
    if biz_type:
        query = query.filter_by(biz_type=biz_type)
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: _paginate_operation_records(query.order_by(OperationLog.id.desc()), page, page_size),
        _operation_record_summary,
    ))


@api_bp.route("/operation-records/<int:record_id>", methods=["GET"])
@login_required
@role_required("advisor", "reviewer", "admin")
def operation_record_detail(record_id):
    record = OperationLog.query.filter_by(id=record_id, user_id=current_user.id).first()
    if not record:
        return fail("处理记录不存在或无权查看", code=40401, status=404)
    return ok({"record": _operation_record_summary(record), "target": _operation_target_summary(record)})


def _pagination_args():
    return parse_pagination_args(
        request.args.get("page", 1),
        request.args.get("page_size", 20),
    )


def _paged_response(loader, serializer):
    page, page_size = _pagination_args()
    result = loader(page, page_size)
    return ok({
        "items": [serializer(item) for item in result.items],
        "page": result.page,
        "page_size": result.page_size,
        "total": result.total,
        "pages": result.pages,
    })


def _paginate_operation_records(query, page, page_size):
    from app.utils.pagination import paginate_query
    return paginate_query(query, page, page_size)


def _application_created_payload(application):
    return {
        "id": application.id,
        "application_no": application.application_no,
        "status": application.status,
    }


def _extension_created_payload(extension):
    application = extension.application
    applicant = application.applicant or application.student
    return {
        "extension_request_id": extension.id,
        "applicant": _student_summary(applicant),
        "applicant_name": applicant.name,
        "status": extension.status,
        "application_status": application.status,
        "extension_days": extension.extension_days,
        "review_level": extension.review_level,
    }


def _extension_review_payload(extension, result_status):
    return {"id": extension.id, "status": result_status}


def _id_status_payload(application):
    return {"id": application.id, "status": application.status}


def _assign_payload(application):
    return {
        "id": application.id,
        "status": application.status,
        "reviewer_teacher_id": application.assigned_teacher_id,
    }


def _reviewer_action_payload(application, review_result):
    return {"id": application.id, "status": application.status, "review_result": review_result}


def _final_approve_payload(application, award):
    return {"id": application.id, "status": application.status, "hour_award_record_id": award.id}


def _credit_exchange_final_payload(application, record):
    return {"id": application.id, "status": application.status, "credit_exchange_record_id": record.id}


def _credit_exchange_created_payload(application):
    payload = {
        "id": application.id,
        "status": application.status,
    }
    if application.rule_id:
        payload["calculated_allocations"] = [_credit_allocation_summary(item) for item in application.allocations]
    return payload


def _appeal_created_payload(appeal):
    return {"id": appeal.id, "appeal_no": appeal.appeal_no, "status": appeal.status}


def _appeal_review_payload(appeal, target):
    return {
        "id": appeal.id,
        "status": appeal.status,
        "next_step": "pending_advisor_reconfirm",
        "target_status": target.status,
    }


def _task_created_payload(task):
    return {"id": task.id, "task_no": task.task_no, "status": task.status}


def _task_registration_created_payload(registration):
    return {"registration_id": registration.id, "status": registration.status}


def _hour_award_summary(award):
    application = award.application
    return {
        "id": award.id,
        "hour_award_record_id": award.id,
        "application_id": award.application_id,
        "application_no": application.application_no if application else None,
        "title": application.title if application else None,
        "leader_student_id": award.leader_student_id,
        "leader": _student_summary(award.leader) if award.leader else None,
        "total_hours": _number(award.total_hours),
        "source_type": award.source_type,
        "is_exchanged": bool(award.is_exchanged),
        "awarded_at": _iso(award.awarded_at),
        "remark": award.remark,
    }


def _credit_exchange_form_payload(award, members, rule, suggested_total_credits, can_submit):
    return {
        "hour_award": _hour_award_summary(award),
        "members": [
            {
                "student": _student_summary(item.student),
                "is_leader": bool(item.is_leader),
                "can_apply_credit_exchange": bool(item.can_apply_credit_exchange),
            }
            for item in members
        ],
        "conversion_rule": _conversion_rule_summary(rule),
        "suggested_total_credits": _number(suggested_total_credits),
        "can_submit": bool(can_submit),
    }


def _credit_exchange_summary(exchange):
    applicant = exchange.applicant or exchange.student
    return {
        "id": exchange.id,
        "exchange_no": exchange.exchange_no,
        "hour_award_record_id": exchange.hour_award_record_id,
        "hour_application_id": exchange.hour_application_id,
        "applicant": _student_summary(applicant) if applicant else None,
        "advisor": _teacher_summary(exchange.advisor) if exchange.advisor else None,
        "total_hours": _number(exchange.total_hours or exchange.requested_hours),
        "estimated_total_credits": _number(exchange.estimated_total_credits or exchange.estimated_credits),
        "status": exchange.status,
        "status_name": exchange.status_name,
        "rule_id": exchange.rule_id,
        "rule_name": (exchange.rule_snapshot or {}).get("rule_name"),
        "created_at": _iso(exchange.created_at),
        "updated_at": _iso(exchange.updated_at),
    }


def _credit_exchange_detail_payload(exchange):
    return {
        "exchange": _credit_exchange_detail(exchange),
        "allocations": [_credit_allocation_summary(item) for item in exchange.allocations],
        "attachments": _credit_exchange_attachments(exchange),
        "actions": {
            "can_advisor_approve": exchange.status == "submitted",
            "can_admin_final": exchange.status == "pending_admin_final",
            "can_appeal": exchange.status in {"final_rejected", "advisor_rejected"},
        },
    }


def _credit_exchange_detail(exchange):
    item = _credit_exchange_summary(exchange)
    item.update(
        {
            "description": exchange.description,
            "hour_award": _hour_award_summary(exchange.hour_award_record) if exchange.hour_award_record else None,
            "rule_snapshot": exchange.rule_snapshot,
            "conversion_rule": _conversion_rule_summary(exchange.conversion_rule) if exchange.conversion_rule else None,
            "advisor_review_comment": exchange.advisor_review_comment,
            "advisor_reviewed_at": _iso(exchange.advisor_reviewed_at),
            "admin_review_comment": exchange.admin_review_comment or exchange.review_comment,
            "admin_reviewed_at": _iso(exchange.admin_reviewed_at or exchange.approved_at),
        }
    )
    return item


def _credit_allocation_summary(allocation):
    return {
        "id": allocation.id,
        "student": _student_summary(allocation.student) if allocation.student else None,
        "student_id": allocation.student_id,
        "allocated_hours": _number(allocation.allocated_hours),
        "credit_type": allocation.credit_type,
        "allocated_credits": _number(allocation.allocated_credits),
        "remark": allocation.remark,
    }


def _credit_exchange_attachments(exchange):
    return [
        _attachment_summary(item)
        for item in Attachment.query.filter_by(
            owner_type="credit_exchange",
            owner_id=exchange.id,
            status="active",
        ).order_by(Attachment.id.asc()).all()
    ]


def _appeal_summary(appeal):
    return {
        "id": appeal.id,
        "appeal_no": appeal.appeal_no,
        "target_type": appeal.target_type,
        "target_id": appeal.target_id,
        "student": _student_summary(appeal.applicant) if appeal.applicant else None,
        "reason": appeal.reason,
        "status": appeal.status,
        "admin_decision": appeal.admin_decision,
        "admin_advice": appeal.admin_advice,
        "reopen_stage": appeal.reopen_stage,
        "standard_rule_file": _rule_file_summary(appeal.standard_rule_file) if appeal.standard_rule_file else None,
        "submitted_at": _iso(appeal.created_at),
        "created_at": _iso(appeal.created_at),
        "reviewed_at": _iso(appeal.reviewed_at),
    }


def _reopened_appeal_payload(appeal, target):
    return {
        "appeal_id": appeal.id,
        "target_id": target.id,
        "target_status": target.status,
        "reopen_stage": appeal.reopen_stage,
    }


def _appeal_detail_payload(appeal):
    return {
        "appeal": _appeal_summary(appeal),
        "target": _appeal_target_summary(appeal),
        "attachments": _owner_attachments("appeal", appeal.id),
    }


def _appeal_target_summary(appeal):
    if appeal.target_type == "hour_application":
        target = get_application(appeal.target_id)
        return _hour_application_summary(target)
    if appeal.target_type == "credit_exchange":
        target = get_admin_credit_exchange(appeal.target_id)
        return _credit_exchange_summary(target)
    return None

def _task_summary(task):
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
        "registration_deadline": _iso(task.registration_deadline),
        "status": task.status,
        "advisor": _teacher_summary(task.advisor) if task.advisor else None,
        "created_at": _iso(task.created_at),
        "updated_at": _iso(task.updated_at),
    }


def _task_leader_payload(task, leader_student_id):
    return {
        "task_id": task.id,
        "leader_student_id": leader_student_id,
        "leader_assigned": True,
        "task_status": task.status,
    }


def _student_team_payload(task, members, student):
    leader = next((item for item in members if item.is_leader), None)
    submission = task.result_submissions[0] if task.result_submissions else None
    return {
        "task": _task_detail(task),
        "members": [_task_member_summary(item) for item in members],
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


def _task_result_created_payload(submission):
    return {
        "submission_id": submission.id,
        "hour_application_id": submission.hour_application_id,
        "status": submission.hour_application.status if submission.hour_application else submission.status,
        "submission_status": submission.status,
    }


def _task_result_summary(submission):
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
        "leader": _student_summary(submission.leader),
        "summary": submission.summary,
        "requested_hours": _number(submission.requested_hours),
        "status": submission.status,
        "hour_application_id": submission.hour_application_id,
        "attachment_count": active_attachment_count,
        "submitted_at": _iso(submission.created_at),
        "updated_at": _iso(submission.updated_at),
    }


def _task_result_detail_payload(submission):
    latest_version = submission.versions[-1] if submission.versions else None
    current_attachment_ids = set(latest_version.attachment_ids or []) if latest_version else set()
    return {
        "submission": {
            "id": submission.id,
            "task_id": submission.task_id,
            "leader_student_id": submission.leader_student_id,
            "summary": submission.summary,
            "requested_hours": _number(submission.requested_hours),
            "status": submission.status,
            "hour_application_id": submission.hour_application_id,
            "advisor_comment": submission.advisor_comment,
            "created_at": _iso(submission.created_at),
            "advisor_reviewed_at": _iso(submission.advisor_reviewed_at),
        },
        "task": _task_detail(submission.task),
        "attachments": [
            item for item in _owner_attachments("task_result", submission.id)
            if not current_attachment_ids or item["id"] in current_attachment_ids
        ],
        "versions": [
            {
                "id": version.id,
                "version_no": version.version_no,
                "summary": version.summary,
                "requested_hours": _number(version.requested_hours),
                "attachment_ids": version.attachment_ids or [],
                "submitted_by": version.submitted_by,
                "submitted_at": _iso(version.created_at),
            }
            for version in submission.versions
        ],
    }


def _complaint_summary(complaint):
    # V1 对管理员保持匿名：响应中不返回提交账号或学生信息。
    return {
        "id": complaint.id,
        "content": complaint.content,
        "status": complaint.status,
        "created_at": _iso(complaint.created_at),
        "viewed_at": _iso(complaint.viewed_at),
    }


def _complaint_detail_payload(complaint):
    return {
        "complaint": _complaint_summary(complaint),
        "attachments": _owner_attachments("complaint", complaint.id),
    }


def _operation_target_summary(record):
    if not record.biz_id:
        return None
    if record.biz_type in {"hour_application", "extension_request"}:
        item = db.session.get(HourApplication, record.biz_id)
        return _hour_application_summary(item) if item else None
    if record.biz_type in {"college_task", "task_registration"}:
        item = db.session.get(CollegeTask, record.biz_id)
        return _task_summary(item) if item else None
    if record.biz_type == "task_result":
        item = db.session.get(TaskResultSubmission, record.biz_id)
        return _task_result_detail_payload(item)["submission"] if item else None
    if record.biz_type == "credit_exchange":
        item = db.session.get(CreditExchangeApplication, record.biz_id)
        return _credit_exchange_summary(item) if item else None
    if record.biz_type == "appeal":
        item = db.session.get(Appeal, record.biz_id)
        return _appeal_summary(item) if item else None
    if record.biz_type == "complaint":
        item = db.session.get(Complaint, record.biz_id)
        return _complaint_summary(item) if item else None
    return None


def _task_detail_payload(task):
    return {
        "task": _task_detail(task),
        "registrations": [_task_registration_summary(item) for item in sorted(task.registrations, key=lambda item: (item.created_at, item.id))],
        "members": [_task_member_summary(item) for item in sorted(task.members, key=lambda item: (not item.is_leader, item.id)) if item.status == "active"],
    }


def _student_task_detail_payload(task, registration):
    payload = _task_detail_payload(task)
    payload["registration"] = _task_registration_summary(registration) if registration else None
    payload["can_register"] = (
        task.status in {"published", "registration_open"}
        and registration is None
        and bool(task.registration_deadline and task.registration_deadline > business_now())
    )
    return payload


def _task_detail(task):
    item = _task_summary(task)
    members = [_task_member_summary(member) for member in task.members if member.status == "active"]
    leader = next((member for member in members if member["is_leader"]), None)
    item.update(
        {
            "major_name": task.major_name,
            "course_name": task.course_name,
            "registration_start_at": _iso(task.registration_start_at),
            "published_at": _iso(task.published_at),
            "admin_review_comment": task.admin_review_comment,
            "registrations": [_task_registration_summary(item) for item in task.registrations],
            "members": members,
            "leader": leader["student"] if leader else None,
            "actions": {
                "can_register": task.status in {"published", "registration_open"}
                and bool(task.registration_deadline and task.registration_deadline > business_now()),
                "can_select": task.status == "selection_pending",
            },
        }
    )
    return item


def _task_registration_summary(registration):
    if not registration:
        return None
    return {
        "id": registration.id,
        "task_id": registration.task_id,
        "student": _student_summary(registration.student) if registration.student else None,
        "student_id": registration.student_id,
        "status": registration.status,
        "reason": registration.apply_reason,
        "submitted_at": _iso(registration.created_at),
        "selected_at": _iso(registration.selected_at),
    }


def _task_member_summary(member):
    return {
        "id": member.id,
        "task_id": member.task_id,
        "registration_id": member.registration_id,
        "student_id": member.student_id,
        "student_name": member.student.name if member.student else None,
        "student": _student_summary(member.student) if member.student else None,
        "is_leader": bool(member.is_leader),
        "selected_at": _iso(member.created_at),
    }


def _hour_application_summary(application):
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
        "applicant": _student_summary(applicant) if applicant else None,
        "applicant_name": applicant.name if applicant else None,
        "leader": _student_summary(application.leader) if application.leader else None,
        "advisor_teacher_id": primary_advisor.teacher_id if primary_advisor else None,
        "requested_hours": _number(application.requested_hours),
        "reviewer_suggested_hours": _number(application.reviewer_suggested_hours),
        "final_hours": _number(application.final_hours),
        "status": application.status,
        "submitted_at": _iso(application.submitted_at),
        "created_at": _iso(application.created_at),
        "updated_at": _iso(application.updated_at),
    }


def _extension_request_payload(extension):
    application = extension.application
    applicant = application.applicant or application.student
    return {
        "id": extension.id,
        "application_id": application.id,
        "applicant": _student_summary(applicant),
        "applicant_name": applicant.name,
        "old_due_at": _iso(extension.old_due_at),
        "requested_due_at": _iso(extension.requested_due_at),
        "extension_days": extension.extension_days,
        "reason": extension.reason,
        "review_level": extension.review_level,
        "status": extension.status,
        "review_comment": extension.review_comment,
        "created_at": _iso(extension.created_at),
        "reviewed_at": _iso(extension.reviewed_at),
    }


def _extension_detail_payload(extension):
    return {
        "extension_request": _extension_request_payload(extension),
        "application": _hour_application_summary(extension.application),
    }


def _admin_hour_application_summary(application):
    item = _hour_application_summary(application)
    item["can_operate"] = application.status in {"pending_assignment", "pending_admin_final"}
    return item


def _pending_final_summary(application):
    item = _hour_application_summary(application)
    result = latest_reviewer_result(application.id)
    item["review_result"] = _review_record(result)["decision"] if result else None
    return item


def _hour_application_detail_payload(application):
    workflow_progress = _hour_application_workflow_progress(application)
    return {
        "id": application.id,
        "application_no": application.application_no,
        "status": application.status,
        "application": _hour_application_detail(application),
        "applicant": _student_summary(application.applicant or application.student),
        "members": _application_members(application),
        "advisors": _application_advisors(application),
        "attachments": _application_attachments(application),
        "reviews": _application_reviews(application),
        "advisor_reviewed_at": _iso(application.advisor_reviewed_at),
        "assigned_at": workflow_progress["admin_assignment"]["completed_at"],
        "reviewer_reviewed_at": _iso(application.reviewer_reviewed_at),
        "final_reviewed_at": _iso(application.final_reviewed_at),
        "workflow_progress": workflow_progress,
        "actions": _action_flags(application),
    }


def _admin_extension_detail_payload(extension):
    application = extension.application
    student = application.applicant or application.student
    return {
        "extension_request_id": extension.id,
        "hour_application_id": application.id,
        "old_due_at": _iso(extension.old_due_at),
        "requested_due_at": _iso(extension.requested_due_at),
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


def _advisor_detail_payload(application):
    payload = _hour_application_detail_payload(application)
    payload["can_operate"] = application.status in {"submitted", "material_submitted"}
    return payload


def _admin_detail_payload(application):
    payload = _hour_application_detail_payload(application)
    payload["assignments"] = _review_assignments(application)
    return payload


def _reviewer_detail_payload(application):
    payload = _hour_application_detail_payload(application)
    payload["requested_hours"] = _number(application.requested_hours)
    payload["can_review"] = application.status == "pending_review"
    return payload


def _final_review_payload(application):
    payload = _hour_application_detail_payload(application)
    result = latest_reviewer_result(application.id)
    payload["reviewer_result"] = _review_record(result) if result else None
    payload["final_hours"] = _number(application.final_hours or application.reviewer_suggested_hours)
    return payload


def _hour_application_detail(application):
    item = _hour_application_summary(application)
    workflow_progress = _hour_application_workflow_progress(application)
    item.update(
        {
            "description": application.description,
            "achievement_summary": application.achievement_summary or application.achievement_submission,
            "major_name": application.major_name,
            "course_name": application.course_name,
            "material_due_at": _iso(application.material_due_at),
            "extension_count": application.extension_count,
            "source_task_id": application.source_task_id,
            "task_result_submission_id": application.task_result_submission_id,
            "assigned_reviewer": _teacher_summary(application.assigned_teacher) if application.assigned_teacher else None,
            "appeal_advice": application.appeal_advice,
            "members": _application_members(application),
            "advisors": _application_advisors(application),
            "attachments": _application_attachments(application),
            "reviews": _application_reviews(application),
            "assignments": _review_assignments(application),
            "advisor_reviewed_at": _iso(application.advisor_reviewed_at),
            "assigned_at": workflow_progress["admin_assignment"]["completed_at"],
            "reviewer_reviewed_at": _iso(application.reviewer_reviewed_at),
            "final_reviewed_at": _iso(application.final_reviewed_at),
            "workflow_progress": workflow_progress,
            "actions": _action_flags(application),
        }
    )
    return item


def _hour_application_workflow_progress(application):
    assignments = sorted(
        getattr(application, "review_assignments", []),
        key=lambda item: (item.assigned_at, item.id),
    )
    latest_assignment = assignments[-1] if assignments else None
    return {
        "student_submission": {
            "completed": bool(application.submitted_at),
            "completed_at": _iso(application.submitted_at),
        },
        "advisor_confirmation": {
            "completed": bool(application.advisor_reviewed_at),
            "completed_at": _iso(application.advisor_reviewed_at),
        },
        "admin_assignment": {
            "completed": latest_assignment is not None,
            "completed_at": _iso(latest_assignment.assigned_at) if latest_assignment else None,
        },
        "reviewer_review": {
            "completed": bool(application.reviewer_reviewed_at),
            "completed_at": _iso(application.reviewer_reviewed_at),
        },
        "admin_final_confirmation": {
            "completed": bool(application.final_reviewed_at),
            "completed_at": _iso(application.final_reviewed_at),
        },
    }


def _application_members(application):
    links = sorted(application.member_links, key=lambda item: (not item.is_leader, item.id))
    return [
        {
            "student": _student_summary(link.student),
            "is_leader": bool(link.is_leader),
            "can_view": bool(link.can_view),
            "joined_at": _iso(link.joined_at),
        }
        for link in links
        if link.status == "active"
    ]


def _application_advisors(application):
    links = sorted(application.advisor_links, key=lambda item: (item.advisor_role != "primary", item.id))
    return [
        {
            "teacher": _teacher_summary(link.teacher),
            "advisor_role": link.advisor_role,
            "can_operate": bool(link.can_operate),
            "reviewed_at": _iso(link.reviewed_at),
        }
        for link in links
    ]


def _application_attachments(application):
    generic_items = Attachment.query.filter_by(
        owner_type="hour_application",
        owner_id=application.id,
        status="active",
    ).order_by(Attachment.id.asc()).all()
    summaries = [_attachment_summary(item) for item in generic_items]
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
        summaries.extend(_attachment_summary(item) for item in task_result_items)
    legacy_summaries = [
        {
            "id": item.id,
            "biz_type": "hour_application",
            "file_name": item.file_name,
            "file_size": item.file_size,
            "mime_type": item.file_type,
            "url": f"/static/{item.static_relative_path}",
            "uploaded_by": item.uploaded_by,
            "created_at": _iso(item.created_at),
        }
        for item in getattr(application, "attachments", [])
    ]
    return summaries + legacy_summaries


def _application_reviews(application):
    reviews = sorted(getattr(application, "reviews", []), key=lambda item: (item.created_at, item.id))
    return [_review_record(item) for item in reviews]


def _review_record(review):
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
        "requested_hours_snapshot": _number(review.requested_hours_snapshot),
        "approved_hours": _number(review.approved_hours),
        "comment": review.comment,
        "created_at": _iso(review.created_at),
    }


def _review_assignments(application):
    assignments = sorted(getattr(application, "review_assignments", []), key=lambda item: (item.assigned_at, item.id))
    return [
        {
            "id": item.id,
            "reviewer": _teacher_summary(item.reviewer),
            "assigned_by_name": None,
            "assign_type": "assign" if item.status == "active" else "reassign",
            "reason": item.assign_reason,
            "created_at": _iso(item.assigned_at),
        }
        for item in assignments
    ]


def _action_flags(application):
    return {
        "can_edit": application.status in {"draft", "advisor_rejected", "reviewer_rejected"},
        "can_submit": application.status in {"draft", "advisor_rejected", "reviewer_rejected"},
        "can_approve": application.status in {"submitted", "material_submitted", "pending_review", "pending_admin_final"},
        "can_reject": application.status in {"submitted", "material_submitted", "pending_review", "pending_admin_final"},
        "can_assign": application.status == "pending_assignment",
        "can_appeal": application.status in {"reviewer_modified_approved", "reviewer_rejected", "final_rejected"},
        "can_download": True,
    }


def _number(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _iso(value):
    return format_api_datetime(value)

