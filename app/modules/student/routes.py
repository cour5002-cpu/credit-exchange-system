from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.core.legacy import block_legacy_write
from app.modules.hour_application.forms import HourApplicationForm
from app.models.student_hour_account import StudentHourAccount
from app.services.hour_account_service import get_total_exchanged_credits
from app.services.form_option_service import get_test_course_map, get_test_major_options, get_test_teacher_map
from app.services.hour_application_service import (
    list_application_attachments,
    list_application_reviews,
    get_student_application_detail,
    get_task_type_choices,
    list_student_applications,
)
from app.services.student_service import get_current_student
from app.utils.permissions import role_required


student_bp = Blueprint("student", __name__, url_prefix="/student")


@student_bp.route("/dashboard")
@login_required
@role_required("student")
def dashboard():
    return render_template("student/dashboard.html")


@student_bp.route("/hour-applications/new", methods=["GET", "POST"])
@login_required
@role_required("student")
def create_hour_application_view():
    if request.method == "POST":
        return block_legacy_write("student.create_hour_application_view")

    student = get_current_student()
    if not student:
        flash("当前账号未绑定学生信息。", "danger")
        return redirect(url_for("student.dashboard"))

    form = HourApplicationForm()

    return render_template(
        "student/hour_application_create.html",
        form=form,
        task_type_options=get_task_type_choices(),
        major_options=get_test_major_options(),
        course_map=get_test_course_map(),
        teacher_map=get_test_teacher_map(),
    )


@student_bp.route("/hour-applications")
@login_required
@role_required("student")
def list_hour_applications():
    student = get_current_student()
    if not student:
        flash("当前账号未绑定学生信息。", "danger")
        return redirect(url_for("student.dashboard"))

    applications = list_student_applications(student.id)
    return render_template("student/hour_application_list.html", applications=applications)


@student_bp.route("/hour-applications/<int:application_id>")
@login_required
@role_required("student")
def hour_application_detail(application_id):
    student = get_current_student()
    if not student:
        flash("当前账号未绑定学生信息。", "danger")
        return redirect(url_for("student.dashboard"))

    application = get_student_application_detail(student.id, application_id)
    if not application:
        flash("未找到对应申请。", "warning")
        return redirect(url_for("student.list_hour_applications"))

    attachments = list_application_attachments(application.id)
    reviews = list_application_reviews(application.id)
    return render_template(
        "student/hour_application_detail.html",
        application=application,
        attachments=attachments,
        reviews=reviews,
    )


@student_bp.route("/hour-account")
@login_required
@role_required("student")
def hour_account():
    student = get_current_student()
    if not student:
        flash("当前账号未绑定学生信息。", "danger")
        return redirect(url_for("student.dashboard"))

    account = StudentHourAccount.query.filter_by(student_id=student.id).first()
    total_exchanged_credits = get_total_exchanged_credits(student.id)
    return render_template(
        "student/hour_account.html",
        account=account,
        total_exchanged_credits=total_exchanged_credits,
    )
