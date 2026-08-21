from app.extensions import db
from app.models.appeal import Appeal
from app.services.notification_service import create_notification
from app.utils.time_utils import business_now


def complete_appeal_for_target(target_type, target_id, reopen_stage, actor_user_id=None):
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
    notify_appeal_completed(appeal, actor_user_id)
    return appeal


def notify_appeal_completed(appeal, actor_user_id=None):
    if not appeal or not appeal.applicant:
        return None
    return create_notification(
        appeal.applicant.user_id, actor_user_id, "appeal", "appeal_completed",
        "申诉处理已完成", f"您的申诉“{appeal.appeal_no}”已形成最终处理结果，请进入详情查看。",
        biz_type="appeal", biz_id=appeal.id,
        payload={"appeal_no": appeal.appeal_no, "status": appeal.status, "reopen_stage": appeal.reopen_stage},
        dedupe_key=f"appeal:{appeal.id}:1:completed",
    )
