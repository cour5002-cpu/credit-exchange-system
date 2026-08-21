import os
import uuid
from decimal import Decimal

from flask import current_app
from sqlalchemy import or_

from app.extensions import db
from app.models.hour_application import HourApplication
from app.models.hour_application_attachment import HourApplicationAttachment
from app.models.hour_application_review import HourApplicationReview
from app.models.task_type import TaskType
from app.models.teacher import Teacher
from app.utils.number_generator import generate_application_no


def get_task_type_choices():
    task_types = (
        TaskType.query.filter_by(status="enabled")
        .order_by(TaskType.sort_order.asc(), TaskType.id.asc())
        .all()
    )
    return [item.type_name for item in task_types]


def create_hour_application(student_id, form, files, uploaded_by):
    application = HourApplication(
        application_no=generate_application_no("HS"),
        student_id=student_id,
        title=form.title.data,
        participant_members="、".join(
            [item.strip() for item in (form.participant_members.data or "").split("||") if item.strip()]
        ),
        major_name=form.major_name.data,
        course_name=form.course_name.data,
        instructor_name=form.instructor_name.data,
        task_type_code=form.task_type_code.data.strip(),
        requested_hours=Decimal(str(form.requested_hours.data)),
        status="submitted",
    )
    db.session.add(application)
    db.session.flush()

    for file_storage in files:
        if not file_storage or not file_storage.filename:
            continue
        attachment = save_attachment(application.id, file_storage, uploaded_by)
        db.session.add(attachment)

    db.session.commit()
    return application


def save_attachment(application_id, file_storage, uploaded_by):
    upload_root = current_app.config["UPLOAD_FOLDER"]
    app_dir = os.path.join(upload_root, "hour_applications")
    os.makedirs(app_dir, exist_ok=True)

    extension = os.path.splitext(file_storage.filename)[1]
    stored_name = f"{uuid.uuid4().hex}{extension}"
    stored_path = os.path.join(app_dir, stored_name)
    file_storage.save(stored_path)

    relative_path = os.path.relpath(stored_path, current_app.root_path).replace("\\", "/")

    return HourApplicationAttachment(
        application_id=application_id,
        file_name=file_storage.filename,
        file_path=relative_path,
        file_size=file_storage.content_length or 0,
        file_type=file_storage.mimetype,
        uploaded_by=uploaded_by,
    )


def list_student_applications(student_id):
    return (
        HourApplication.query.filter_by(student_id=student_id)
        .order_by(HourApplication.created_at.desc(), HourApplication.id.desc())
        .all()
    )


def get_student_application_detail(student_id, application_id):
    return HourApplication.query.filter_by(id=application_id, student_id=student_id).first()


def list_all_applications(status=None):
    query = HourApplication.query
    if status:
        query = query.filter_by(status=status)
    return query.order_by(HourApplication.created_at.desc(), HourApplication.id.desc()).all()


def get_application_by_id(application_id):
    return HourApplication.query.filter_by(id=application_id).first()


def get_teacher_choices():
    teachers = Teacher.query.filter_by(status="active").order_by(Teacher.id.asc()).all()
    return [
        (
            teacher.id,
            f"{teacher.name}（{teacher.teacher_no} / {teacher.major_name or '未设置专业'} / {teacher.course_name or '未设置课程'}）",
        )
        for teacher in teachers
    ]


def get_filtered_teacher_choices(major_name=None, course_name=None, keyword=None):
    query = Teacher.query.filter_by(status="active")
    if major_name:
        query = query.filter(Teacher.major_name.contains(major_name))
    if course_name:
        query = query.filter(Teacher.course_name.contains(course_name))
    if keyword:
        query = query.filter(
            or_(
                Teacher.name.contains(keyword),
                Teacher.teacher_no.contains(keyword),
                Teacher.major_name.contains(keyword),
                Teacher.course_name.contains(keyword),
            )
        )
    teachers = query.order_by(Teacher.id.asc()).all()
    return [
        (
            teacher.id,
            f"{teacher.name}（{teacher.teacher_no} / {teacher.major_name or '未设置专业'} / {teacher.course_name or '未设置课程'}）",
        )
        for teacher in teachers
    ]


def assign_teacher(application, teacher_id):
    application.assigned_teacher_id = teacher_id
    application.status = "assigned"
    db.session.commit()


def list_assigned_applications(teacher_id):
    return (
        HourApplication.query.filter_by(assigned_teacher_id=teacher_id, status="assigned")
        .order_by(HourApplication.created_at.desc(), HourApplication.id.desc())
        .all()
    )


def list_application_attachments(application_id):
    return (
        HourApplicationAttachment.query.filter_by(application_id=application_id)
        .order_by(HourApplicationAttachment.id.asc())
        .all()
    )


def list_application_reviews(application_id):
    return (
        HourApplicationReview.query.filter_by(application_id=application_id)
        .order_by(HourApplicationReview.created_at.asc(), HourApplicationReview.id.asc())
        .all()
    )
