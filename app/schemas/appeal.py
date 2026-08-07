from app.schemas.base import owner_attachments, rule_file_summary, student_summary
from app.schemas.common import iso
from app.schemas.credit_exchange import credit_exchange_summary
from app.schemas.hour_application import hour_application_summary


def appeal_created_payload(appeal):
    return {"id": appeal.id, "appeal_no": appeal.appeal_no, "status": appeal.status}


def appeal_review_payload(appeal, target):
    return {
        "id": appeal.id,
        "status": appeal.status,
        "next_step": "pending_advisor_reconfirm",
        "target_status": target.status,
    }


def appeal_summary(appeal):
    return {
        "id": appeal.id,
        "appeal_no": appeal.appeal_no,
        "target_type": appeal.target_type,
        "target_id": appeal.target_id,
        "student": student_summary(appeal.applicant) if appeal.applicant else None,
        "reason": appeal.reason,
        "status": appeal.status,
        "admin_decision": appeal.admin_decision,
        "admin_advice": appeal.admin_advice,
        "reopen_stage": appeal.reopen_stage,
        "standard_rule_file": rule_file_summary(appeal.standard_rule_file)
        if appeal.standard_rule_file else None,
        "submitted_at": iso(appeal.created_at),
        "created_at": iso(appeal.created_at),
        "reviewed_at": iso(appeal.reviewed_at),
    }


def reopened_appeal_payload(appeal, target):
    return {
        "appeal_id": appeal.id,
        "target_id": target.id,
        "target_status": target.status,
        "reopen_stage": appeal.reopen_stage,
    }


def appeal_detail_payload(appeal, target):
    return {
        "appeal": appeal_summary(appeal),
        "target": appeal_target_summary(appeal.target_type, target),
        "attachments": owner_attachments("appeal", appeal.id),
    }


def appeal_target_summary(target_type, target):
    if target_type == "hour_application":
        return hour_application_summary(target)
    if target_type == "credit_exchange":
        return credit_exchange_summary(target)
    return None
