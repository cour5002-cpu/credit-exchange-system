from app.extensions import db
from app.models.appeal import Appeal
from app.models.college_task import CollegeTask
from app.models.complaint import Complaint
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.hour_application import HourApplication
from app.models.task_result_submission import TaskResultSubmission
from app.schemas.base import operation_record_summary
from app.schemas.appeal import appeal_summary
from app.schemas.college_task import task_result_detail_payload, task_summary
from app.schemas.complaint import complaint_summary
from app.schemas.credit_exchange import credit_exchange_summary
from app.schemas.hour_application import hour_application_summary


def operation_target_summary(record):
    if not record.biz_id:
        return None
    if record.biz_type in {"hour_application", "extension_request"}:
        item = db.session.get(HourApplication, record.biz_id)
        return hour_application_summary(item) if item else None
    if record.biz_type in {"college_task", "task_registration"}:
        item = db.session.get(CollegeTask, record.biz_id)
        return task_summary(item) if item else None
    if record.biz_type == "task_result":
        item = db.session.get(TaskResultSubmission, record.biz_id)
        return task_result_detail_payload(item)["submission"] if item else None
    if record.biz_type == "credit_exchange":
        item = db.session.get(CreditExchangeApplication, record.biz_id)
        return credit_exchange_summary(item) if item else None
    if record.biz_type == "appeal":
        item = db.session.get(Appeal, record.biz_id)
        return appeal_summary(item) if item else None
    if record.biz_type == "complaint":
        item = db.session.get(Complaint, record.biz_id)
        return complaint_summary(item) if item else None
    return None
