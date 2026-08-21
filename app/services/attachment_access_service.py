from app.extensions import db
from app.models.appeal import Appeal
from app.models.application_advisor import ApplicationAdvisor
from app.models.college_task import CollegeTask
from app.models.credit_exchange_allocation import CreditExchangeAllocation
from app.models.credit_exchange_application import CreditExchangeApplication
from app.models.extension_request import ExtensionRequest
from app.models.hour_application import HourApplication
from app.models.hour_application_member import HourApplicationMember
from app.models.review_assignment import ReviewAssignment
from app.models.student import Student
from app.models.task_member import TaskMember
from app.models.task_result_submission import TaskResultSubmission
from app.models.teacher import Teacher


STUDENT_VISIBLE_TASK_ATTACHMENT_STATUSES = {
    "published",
    "registration_open",
    "registration_closed",
    "selection_pending",
    "leader_pending",
    "task_in_progress",
    "result_submitted",
    "result_approved",
}


def can_access_attachment(user, attachment):
    if attachment.uploaded_by == user.id or user.has_role("admin"):
        return True
    if not attachment.owner_type or not attachment.owner_id:
        return False
    if attachment.owner_type == "rule_file":
        return True

    student = Student.query.filter_by(user_id=user.id).first()
    teacher = Teacher.query.filter_by(user_id=user.id).first()

    if attachment.owner_type == "hour_application":
        return _can_access_hour_application(student, teacher, attachment.owner_id)
    if attachment.owner_type == "extension_request":
        return _can_access_extension(student, teacher, attachment.owner_id)
    if attachment.owner_type == "college_task":
        return _can_access_college_task(student, teacher, attachment.owner_id)
    if attachment.owner_type == "task_result":
        return _can_access_task_result(student, teacher, attachment.owner_id)
    if attachment.owner_type == "credit_exchange":
        return _can_access_credit_exchange(student, teacher, attachment.owner_id)
    if attachment.owner_type == "appeal":
        return _can_access_appeal(student, teacher, attachment.owner_id)
    return False


def _can_access_hour_application(student, teacher, application_id):
    application = db.session.get(HourApplication, application_id)
    if not application:
        return False
    if student and (
        student.id in {
            application.student_id,
            application.applicant_student_id,
            application.leader_student_id,
        }
        or HourApplicationMember.query.filter_by(
            application_id=application.id,
            student_id=student.id,
            status="active",
        ).first()
    ):
        return True
    return bool(teacher and (
        application.assigned_teacher_id == teacher.id
        or ApplicationAdvisor.query.filter_by(
            application_id=application.id,
            teacher_id=teacher.id,
        ).first()
    ))


def _can_access_extension(student, teacher, extension_id):
    extension = db.session.get(ExtensionRequest, extension_id)
    if not extension:
        return False
    application = extension.application
    if student and student.id in {
        application.student_id,
        application.applicant_student_id,
        application.leader_student_id,
    }:
        return True
    return bool(teacher and ApplicationAdvisor.query.filter_by(
        application_id=application.id,
        teacher_id=teacher.id,
    ).first())


def _can_access_college_task(student, teacher, task_id):
    task = db.session.get(CollegeTask, task_id)
    if not task:
        return False
    if student:
        return task.status in STUDENT_VISIBLE_TASK_ATTACHMENT_STATUSES
    return bool(teacher and task.advisor_teacher_id == teacher.id)


def _can_access_task_result(student, teacher, submission_id):
    submission = db.session.get(TaskResultSubmission, submission_id)
    if not submission:
        return False
    if student and TaskMember.query.filter_by(
        task_id=submission.task_id,
        student_id=student.id,
        status="active",
    ).first():
        return True
    if not teacher:
        return False
    if submission.task.advisor_teacher_id == teacher.id:
        return True
    application = submission.hour_application
    if not application:
        return False
    if application.assigned_teacher_id == teacher.id:
        return True
    return ReviewAssignment.query.filter_by(
        application_id=application.id,
        reviewer_teacher_id=teacher.id,
        status="active",
    ).first() is not None


def _can_access_credit_exchange(student, teacher, exchange_id):
    exchange = db.session.get(CreditExchangeApplication, exchange_id)
    if not exchange:
        return False
    if student and (
        student.id in {exchange.student_id, exchange.applicant_student_id}
        or CreditExchangeAllocation.query.filter_by(
            exchange_application_id=exchange.id,
            student_id=student.id,
        ).first()
    ):
        return True
    return bool(teacher and exchange.advisor_teacher_id == teacher.id)


def _can_access_appeal(student, teacher, appeal_id):
    appeal = db.session.get(Appeal, appeal_id)
    if not appeal:
        return False
    if student and appeal.applicant_student_id == student.id:
        return True
    if not teacher:
        return False
    if appeal.target_type == "hour_application":
        target = db.session.get(HourApplication, appeal.target_id)
        return bool(target and (
            target.assigned_teacher_id == teacher.id
            or ApplicationAdvisor.query.filter_by(
                application_id=target.id,
                teacher_id=teacher.id,
            ).first()
        ))
    if appeal.target_type == "credit_exchange":
        target = db.session.get(CreditExchangeApplication, appeal.target_id)
        return bool(target and target.advisor_teacher_id == teacher.id)
    return False
