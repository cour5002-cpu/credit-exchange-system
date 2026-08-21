from app.schemas.common import iso
from app.models.student import Student
from app.utils.time_utils import business_now


def admin_dashboard_payload(sections):
    counts = {section.todo_type: section.count for section in sections}
    return {
        "generated_at": iso(business_now()),
        "refresh_interval_seconds": 60,
        "total_pending": sum(counts.values()),
        "counts": counts,
        "sections": [
            {
                "todo_type": section.todo_type,
                "label": section.label,
                "count": section.count,
                "list_api": section.list_api,
                "items": [_preview_item(section.todo_type, item) for item in section.items],
            }
            for section in sections
        ],
    }


def _preview_item(todo_type, item):
    biz_no, title, submitted_by = _preview_identity(todo_type, item)
    return {
        "biz_id": item.id,
        "biz_no": biz_no,
        "title": title,
        "status": item.status,
        "submitted_by": submitted_by,
        "created_at": iso(item.created_at),
    }


def _preview_identity(todo_type, item):
    if todo_type == "task_publish_review":
        return item.task_no, item.title, item.publisher.real_name if item.publisher else None
    if todo_type in {"hour_review_assignment", "hour_final_confirmation"}:
        applicant = item.applicant or item.student
        return item.application_no, item.title, applicant.name if applicant else None
    if todo_type == "credit_final_confirmation":
        applicant = item.applicant or item.student
        return item.exchange_no, "学分兑换申请", applicant.name if applicant else None
    if todo_type in {"appeal_initial_review", "appeal_review_assignment", "appeal_final_confirmation"}:
        if todo_type == "appeal_initial_review":
            title = "课时申诉" if item.target_type == "hour_application" else "学分兑换申诉"
        elif todo_type == "appeal_review_assignment":
            title = "课时申诉复审分配"
        else:
            title = "课时申诉复审终审"
        return item.appeal_no, title, item.applicant.name if item.applicant else None
    if todo_type == "special_extension_review":
        application = item.application
        applicant = application.applicant or application.student
        return application.application_no, application.title, applicant.name if applicant else None
    student = Student.query.filter_by(user_id=item.submitter_user_id).first()
    category_labels = {
        "personnel_behavior": "人员行为",
        "service_quality": "服务质量",
        "process_violation": "流程违规",
        "other": "其他问题",
    }
    title = f"{category_labels.get(item.category, '其他问题')}：{item.content[:30]}"
    submitted_by = student.name if student else (item.submitter.real_name if item.submitter else None)
    return item.complaint_no, title, submitted_by
