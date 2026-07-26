from app.extensions import db
from app.models.appeal import Appeal
from app.utils.time_utils import business_now


def complete_appeal_for_target(target_type, target_id, reopen_stage):
    appeal = Appeal.query.filter_by(
        target_type=target_type,
        target_id=target_id,
        status="processing",
    ).first()
    if not appeal:
        return None
    appeal.status = "completed"
    appeal.reopen_stage = reopen_stage
    appeal.reviewed_at = appeal.reviewed_at or business_now()
    db.session.add(appeal)
    return appeal
