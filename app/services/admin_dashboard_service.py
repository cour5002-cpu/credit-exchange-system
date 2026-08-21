from dataclasses import dataclass

from app.models.appeal import Appeal
from app.models.college_task import CollegeTask
from app.models.complaint import Complaint
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.extension_request import ExtensionRequest
from app.models.hour_application import HourApplication
from app.services.appeal_workflow import exclude_active_reopened_appeals


@dataclass(frozen=True)
class DashboardSection:
    todo_type: str
    label: str
    list_api: str
    count: int
    items: list


SECTION_DEFINITIONS = (
    ("task_publish_review", "任务发布确认", "/api/v1/admin/task-publish-requests"),
    ("hour_review_assignment", "审核分配", "/api/v1/admin/hour-applications/pending-assignment"),
    ("hour_final_confirmation", "课时最终确认", "/api/v1/admin/hour-applications/pending-final"),
    ("credit_final_confirmation", "学分兑换最终确认", "/api/v1/admin/credit-exchanges/pending-final"),
    ("appeal_initial_review", "申诉初审", "/api/v1/admin/appeals?status=pending_admin_review"),
    ("appeal_review_assignment", "申诉复审核分配", "/api/v1/admin/appeals/reopened/pending-assignment"),
    ("appeal_final_confirmation", "申诉复审最终确认", "/api/v1/admin/appeals/reopened/pending-final"),
    ("special_extension_review", "特殊延期审核", "/api/v1/admin/extension-requests/pending-special"),
    ("complaint_unviewed", "待处理投诉", "/api/v1/admin/complaints?status=pending"),
)


def get_admin_dashboard_sections():
    queries = _section_queries()
    sections = []
    for todo_type, label, list_api in SECTION_DEFINITIONS:
        query = queries[todo_type]
        sections.append(DashboardSection(
            todo_type=todo_type,
            label=label,
            list_api=list_api,
            count=query.count(),
            items=query.order_by(_created_column(todo_type).desc(), _id_column(todo_type).desc()).limit(5).all(),
        ))
    return sections


def _section_queries():
    ordinary_assignment = exclude_active_reopened_appeals(
        HourApplication.query.filter_by(status="pending_assignment")
    )
    ordinary_final = exclude_active_reopened_appeals(
        HourApplication.query.filter_by(status="pending_admin_final")
    )
    return {
        "task_publish_review": CollegeTask.query.filter_by(status="pending_publish_review"),
        "hour_review_assignment": ordinary_assignment,
        "hour_final_confirmation": ordinary_final,
        "credit_final_confirmation": CreditExchangeApplication.query.filter_by(status="pending_admin_final"),
        "appeal_initial_review": Appeal.query.filter_by(status="pending_admin_review"),
        "appeal_review_assignment": Appeal.query.filter_by(
            status="processing", reopen_stage="pending_assignment", target_type="hour_application"
        ),
        "appeal_final_confirmation": Appeal.query.filter_by(
            status="processing", reopen_stage="pending_admin_final", target_type="hour_application"
        ).join(HourApplication, HourApplication.id == Appeal.target_id).filter(
            HourApplication.status == "pending_admin_final"
        ),
        "special_extension_review": ExtensionRequest.query.filter_by(
            review_level="admin", status="pending_admin_review"
        ),
        "complaint_unviewed": Complaint.query.filter(Complaint.status.in_(["submitted", "processing"])),
    }


def _created_column(todo_type):
    if todo_type == "task_publish_review":
        return CollegeTask.created_at
    if todo_type in {"hour_review_assignment", "hour_final_confirmation"}:
        return HourApplication.created_at
    if todo_type == "credit_final_confirmation":
        return CreditExchangeApplication.created_at
    if todo_type in {"appeal_initial_review", "appeal_review_assignment", "appeal_final_confirmation"}:
        return Appeal.created_at
    if todo_type == "special_extension_review":
        return ExtensionRequest.created_at
    return Complaint.created_at


def _id_column(todo_type):
    if todo_type == "task_publish_review":
        return CollegeTask.id
    if todo_type in {"hour_review_assignment", "hour_final_confirmation"}:
        return HourApplication.id
    if todo_type == "credit_final_confirmation":
        return CreditExchangeApplication.id
    if todo_type in {"appeal_initial_review", "appeal_review_assignment", "appeal_final_confirmation"}:
        return Appeal.id
    if todo_type == "special_extension_review":
        return ExtensionRequest.id
    return Complaint.id
