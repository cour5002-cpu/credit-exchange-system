from flask import request
from flask_login import current_user, login_required

from app.core.responses import handle_business as _handle_business, ok
from app.models.task_member import TaskMember
from app.modules.api.blueprint import api_bp
from app.modules.api.payloads import (
    _paged_response,
    _student_task_detail_payload,
    _student_team_payload,
    _task_created_payload,
    _task_detail_payload,
    _task_leader_payload,
    _task_member_summary,
    _task_registration_created_payload,
    _task_registration_summary,
    _task_result_created_payload,
    _task_result_detail_payload,
    _task_result_summary,
    _task_summary,
)
from app.services.week5_appeal_task_service import (
    admin_approve_task_publish,
    admin_reject_task_publish,
    assign_task_leader,
    create_task,
    get_admin_task,
    get_advisor_task,
    get_advisor_task_result,
    get_student_registration,
    get_student_task,
    get_student_team,
    list_admin_tasks,
    list_advisor_task_results,
    list_advisor_tasks,
    list_my_tasks,
    list_pending_task_publish_requests,
    list_student_tasks,
    list_task_registrations_for_advisor,
    register_task,
    resubmit_task_result,
    review_task_result,
    selected_task_members,
    select_task_registrations,
    submit_task_result,
)
from app.utils.permissions import role_required


@api_bp.route("/admin/tasks/drafts", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_task_draft():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(create_task(current_user, data, "admin", submit=False))))


@api_bp.route("/admin/tasks", methods=["POST"])
@login_required
@role_required("admin")
def admin_create_task():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(create_task(current_user, data, "admin", submit=True))))


@api_bp.route("/admin/tasks", methods=["GET"])
@login_required
@role_required("admin")
def admin_tasks():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_admin_tasks(status, page, page_size),
        _task_summary,
    ))


@api_bp.route("/admin/tasks/<int:task_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_task_detail(task_id):
    return _handle_business(lambda: ok(_task_detail_payload(get_admin_task(task_id))))


@api_bp.route("/advisor/tasks/drafts", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_create_task_draft():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(create_task(current_user, data, "teacher", submit=False))))


@api_bp.route("/advisor/tasks", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_create_task():
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(create_task(current_user, data, "teacher", submit=True))))


@api_bp.route("/advisor/tasks", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_tasks():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: ok({"items": [_task_summary(item) for item in list_advisor_tasks(current_user, status)]}))


@api_bp.route("/advisor/tasks/<int:task_id>", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_task_detail(task_id):
    return _handle_business(lambda: ok(_task_detail_payload(get_advisor_task(current_user, task_id))))


@api_bp.route("/advisor/tasks/<int:task_id>/registrations", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_task_registrations(task_id):
    return _handle_business(lambda: ok({"items": [_task_registration_summary(item) for item in list_task_registrations_for_advisor(current_user, task_id)]}))


@api_bp.route("/advisor/tasks/<int:task_id>/registrations/select", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_select_task_registrations(task_id):
    data = request.get_json(silent=True) or {}

    def payload():
        task = select_task_registrations(current_user, task_id, data)
        selected_count = TaskMember.query.filter_by(task_id=task.id, status="active").count()
        return ok({"selected_count": selected_count, "task_status": task.status})

    return _handle_business(payload)


@api_bp.route("/advisor/tasks/<int:task_id>/selected-members", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_selected_task_members(task_id):
    def payload():
        _, members = selected_task_members(current_user, task_id)
        return ok({"items": [_task_member_summary(item) for item in members]})

    return _handle_business(payload)


@api_bp.route("/advisor/tasks/<int:task_id>/leader", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_assign_task_leader(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_leader_payload(*assign_task_leader(current_user, task_id, data.get("leader_student_id")))))


@api_bp.route("/advisor/task-result-submissions/<int:submission_id>", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_task_result_detail(submission_id):
    return _handle_business(lambda: ok(_task_result_detail_payload(get_advisor_task_result(current_user, submission_id))))


@api_bp.route("/advisor/task-result-submissions", methods=["GET"])
@login_required
@role_required("advisor")
def advisor_task_results():
    raw_status = request.args.get("status")
    status = "submitted" if raw_status is None else raw_status.strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_advisor_task_results(current_user, status, page, page_size),
        _task_result_summary,
    ))


@api_bp.route("/advisor/task-result-submissions/<int:submission_id>/approve", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_approve_task_result(submission_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_result_created_payload(review_task_result(current_user, submission_id, True, data.get("comment")))))


@api_bp.route("/advisor/task-result-submissions/<int:submission_id>/reject", methods=["POST"])
@login_required
@role_required("advisor")
def advisor_reject_task_result(submission_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_result_created_payload(review_task_result(current_user, submission_id, False, data.get("comment")))))


@api_bp.route("/student/tasks", methods=["GET"])
@login_required
@role_required("student")
def student_tasks():
    keyword = (request.args.get("keyword") or "").strip() or None
    task_type_id = (request.args.get("task_type_id") or "").strip() or None
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_student_tasks(current_user, keyword, task_type_id, page, page_size),
        _task_summary,
    ))


@api_bp.route("/student/tasks/<int:task_id>", methods=["GET"])
@login_required
@role_required("student")
def student_task_detail(task_id):
    return _handle_business(lambda: ok(_student_task_detail_payload(*get_student_task(current_user, task_id))))


@api_bp.route("/student/tasks/<int:task_id>/team", methods=["GET"])
@login_required
@role_required("student")
def student_task_team(task_id):
    return _handle_business(lambda: ok(_student_team_payload(*get_student_team(current_user, task_id))))


@api_bp.route("/student/tasks/<int:task_id>/result-submissions", methods=["POST"])
@login_required
@role_required("student")
def student_submit_task_result(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_result_created_payload(submit_task_result(current_user, task_id, data))))


@api_bp.route("/student/task-result-submissions/<int:submission_id>/resubmit", methods=["POST"])
@login_required
@role_required("student")
def student_resubmit_task_result(submission_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_result_created_payload(resubmit_task_result(current_user, submission_id, data))))


@api_bp.route("/student/tasks/<int:task_id>/registrations", methods=["POST"])
@login_required
@role_required("student")
def student_register_task(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_registration_created_payload(register_task(current_user, task_id, data))))


@api_bp.route("/student/my-tasks", methods=["GET"])
@login_required
@role_required("student")
def student_my_tasks():
    status = (request.args.get("status") or "").strip() or None
    return _handle_business(lambda: ok({"items": [_task_summary(item) for item in list_my_tasks(current_user, status)]}))


@api_bp.route("/student/task-registrations/<int:registration_id>", methods=["GET"])
@login_required
@role_required("student")
def student_task_registration_detail(registration_id):
    registration = get_student_registration(current_user, registration_id)
    return _handle_business(lambda: ok({"registration": _task_registration_summary(registration), "status": registration.status}))


@api_bp.route("/admin/task-publish-requests", methods=["GET"])
@login_required
@role_required("admin")
def admin_task_publish_requests():
    return _handle_business(lambda: _paged_response(
        lambda page, page_size: list_pending_task_publish_requests(page, page_size),
        _task_summary,
    ))


@api_bp.route("/admin/task-publish-requests/<int:task_id>", methods=["GET"])
@login_required
@role_required("admin")
def admin_task_publish_request_detail(task_id):
    return _handle_business(lambda: ok(_task_detail_payload(get_admin_task(task_id))))


@api_bp.route("/admin/task-publish-requests/<int:task_id>/approve", methods=["POST"])
@login_required
@role_required("admin")
def admin_approve_task_publish_api(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(admin_approve_task_publish(current_user, task_id, data.get("comment")))))


@api_bp.route("/admin/task-publish-requests/<int:task_id>/reject", methods=["POST"])
@login_required
@role_required("admin")
def admin_reject_task_publish_api(task_id):
    data = request.get_json(silent=True) or {}
    return _handle_business(lambda: ok(_task_created_payload(admin_reject_task_publish(current_user, task_id, data.get("comment")))))
