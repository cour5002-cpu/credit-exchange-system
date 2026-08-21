from app.core.errors import BusinessError
from app.extensions import db
from app.models.appeal import Appeal
from app.models.hour_application import HourApplication


def exclude_active_reopened_appeals(query):
    """Keep ordinary hour-application worklists separate from appeal worklists."""
    active_appeal = db.session.query(Appeal.id).filter(
        Appeal.target_type == "hour_application",
        Appeal.target_id == HourApplication.id,
        Appeal.status == "processing",
    ).exists()
    return query.filter(~active_appeal)


def require_hour_application_workflow(application_id, appeal_id=None):
    """Reject ordinary actions when an application belongs to an active appeal."""
    active_appeal = Appeal.query.filter_by(
        target_type="hour_application",
        target_id=application_id,
        status="processing",
    ).first()
    if active_appeal and active_appeal.id != appeal_id:
        raise BusinessError(
            "该申请正在申诉复审，请使用申诉复审入口",
            code=40901,
            status=409,
        )
    return active_appeal


def reconcile_reopened_hour_appeals():
    """Advance appeal stages left behind by legacy ordinary-entry operations."""
    changed = False
    rows = (
        db.session.query(Appeal, HourApplication)
        .join(HourApplication, HourApplication.id == Appeal.target_id)
        .filter(
            Appeal.target_type == "hour_application",
            Appeal.status == "processing",
        )
        .all()
    )
    stage_order = {
        "pending_advisor_confirmation": 0,
        "pending_assignment": 1,
        "pending_reviewer_review": 2,
        "pending_admin_final": 3,
    }
    target_stage = {
        "pending_assignment": "pending_assignment",
        "pending_review": "pending_reviewer_review",
        "pending_admin_final": "pending_admin_final",
    }
    completed_stage = {
        "advisor_rejected": "advisor_rejected",
        "reviewer_rejected": "reviewer_rejected",
        "final_approved": "completed",
        "final_rejected": "completed",
    }

    for appeal, application in rows:
        completed = completed_stage.get(application.status)
        if completed:
            appeal.status = "completed"
            appeal.reopen_stage = completed
            changed = True
            continue

        expected_stage = target_stage.get(application.status)
        if not expected_stage:
            continue
        current_order = stage_order.get(appeal.reopen_stage, -1)
        expected_order = stage_order[expected_stage]
        if expected_order > current_order:
            appeal.reopen_stage = expected_stage
            changed = True

    if changed:
        db.session.commit()
    return changed
