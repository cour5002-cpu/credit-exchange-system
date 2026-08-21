from app.models.attachment import Attachment
from app.schemas.base import (
    attachment_summary,
    conversion_rule_summary,
    student_summary,
    teacher_summary,
)
from app.schemas.common import iso, number


def credit_exchange_final_payload(application, record):
    return {
        "id": application.id,
        "status": application.status,
        "credit_exchange_record_id": record.id,
    }


def credit_exchange_created_payload(application):
    payload = {"id": application.id, "status": application.status}
    if application.rule_id:
        payload["calculated_allocations"] = [
            credit_allocation_summary(item) for item in application.allocations
        ]
    return payload


def hour_award_summary(award):
    application = award.application
    return {
        "id": award.id,
        "hour_award_record_id": award.id,
        "application_id": award.application_id,
        "application_no": application.application_no if application else None,
        "title": application.title if application else None,
        "leader_student_id": award.leader_student_id,
        "leader": student_summary(award.leader) if award.leader else None,
        "total_hours": number(award.total_hours),
        "source_type": award.source_type,
        "is_exchanged": bool(award.is_exchanged),
        "awarded_at": iso(award.awarded_at),
        "remark": award.remark,
    }


def credit_exchange_form_payload(award, members, rule, suggested_total_credits, can_submit):
    return {
        "hour_award": hour_award_summary(award),
        "members": [
            {
                "student": student_summary(item.student),
                "is_leader": bool(item.is_leader),
                "can_apply_credit_exchange": bool(item.can_apply_credit_exchange),
            }
            for item in members
        ],
        "conversion_rule": conversion_rule_summary(rule),
        "suggested_total_credits": number(suggested_total_credits),
        "can_submit": bool(can_submit),
    }


def credit_exchange_summary(exchange):
    applicant = exchange.applicant or exchange.student
    return {
        "id": exchange.id,
        "exchange_no": exchange.exchange_no,
        "hour_award_record_id": exchange.hour_award_record_id,
        "hour_application_id": exchange.hour_application_id,
        "applicant": student_summary(applicant) if applicant else None,
        "advisor": teacher_summary(exchange.advisor) if exchange.advisor else None,
        "total_hours": number(exchange.total_hours or exchange.requested_hours),
        "estimated_total_credits": number(
            exchange.estimated_total_credits or exchange.estimated_credits
        ),
        "status": exchange.status,
        "status_name": exchange.status_name,
        "rule_id": exchange.rule_id,
        "rule_name": (exchange.rule_snapshot or {}).get("rule_name"),
        "created_at": iso(exchange.created_at),
        "updated_at": iso(exchange.updated_at),
    }


def credit_exchange_detail_payload(exchange):
    return {
        "exchange": credit_exchange_detail(exchange),
        "allocations": [credit_allocation_summary(item) for item in exchange.allocations],
        "attachments": credit_exchange_attachments(exchange),
        "actions": {
            "can_advisor_approve": exchange.status == "submitted",
            "can_admin_final": exchange.status == "pending_admin_final",
            "can_appeal": exchange.status in {"final_rejected", "advisor_rejected"},
        },
    }


def credit_exchange_detail(exchange):
    item = credit_exchange_summary(exchange)
    item.update({
        "description": exchange.description,
        "hour_award": hour_award_summary(exchange.hour_award_record)
        if exchange.hour_award_record else None,
        "rule_snapshot": exchange.rule_snapshot,
        "conversion_rule": conversion_rule_summary(exchange.conversion_rule)
        if exchange.conversion_rule else None,
        "advisor_review_comment": exchange.advisor_review_comment,
        "advisor_reviewed_at": iso(exchange.advisor_reviewed_at),
        "admin_review_comment": exchange.admin_review_comment or exchange.review_comment,
        "admin_reviewed_at": iso(exchange.admin_reviewed_at or exchange.approved_at),
    })
    return item


def credit_allocation_summary(allocation):
    return {
        "id": allocation.id,
        "student": student_summary(allocation.student) if allocation.student else None,
        "student_id": allocation.student_id,
        "allocated_hours": number(allocation.allocated_hours),
        "credit_type": allocation.credit_type,
        "allocated_credits": number(allocation.allocated_credits),
        "remark": allocation.remark,
    }


def credit_exchange_attachments(exchange):
    return [
        attachment_summary(item)
        for item in Attachment.query.filter_by(
            owner_type="credit_exchange",
            owner_id=exchange.id,
            status="active",
        ).order_by(Attachment.id.asc()).all()
    ]
