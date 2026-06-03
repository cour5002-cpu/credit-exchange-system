from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.modules.teacher.forms import ReviewHourApplicationForm
from app.models.hour_application import HourApplication
from app.services.hour_application_service import (
    list_application_attachments,
    list_application_reviews,
    list_assigned_applications,
)
from app.services.review_service import get_teacher_application_detail, submit_review
from app.services.teacher_service import get_current_teacher
from app.utils.permissions import role_required


teacher_bp = Blueprint("teacher", __name__, url_prefix="/teacher")


@teacher_bp.route("/dashboard")
@login_required
@role_required("teacher")
def dashboard():
    return render_template("teacher/dashboard.html")


@teacher_bp.route("/hour-applications")
@login_required
@role_required("teacher")
def list_my_applications():
    teacher = get_current_teacher()
    applications = []
    if teacher:
        applications = list_assigned_applications(teacher.id)
    return render_template("teacher/review_list.html", applications=applications)


@teacher_bp.route("/hour-applications/history")
@login_required
@role_required("teacher")
def review_history():
    teacher = get_current_teacher()
    applications = []
    if teacher:
        applications = (
            HourApplication.query.filter_by(assigned_teacher_id=teacher.id)
            .filter(HourApplication.status.in_(["approved", "rejected"]))
            .order_by(
                HourApplication.reviewed_at.desc(),
                HourApplication.id.desc(),
            )
            .all()
        )
    return render_template("teacher/review_history.html", applications=applications)


@teacher_bp.route("/hour-applications/<int:application_id>/next")
@login_required
@role_required("teacher")
def next_application(application_id):
    teacher = get_current_teacher()
    if not teacher:
        flash("当前账号未绑定教师信息。", "danger")
        return redirect(url_for("teacher.dashboard"))

    applications = list_assigned_applications(teacher.id)
    if applications:
        return redirect(url_for("teacher.review_application_detail", application_id=applications[0].id))

    flash("已经是最后一个待审核申请了。", "info")
    return redirect(url_for("teacher.review_application_detail", application_id=application_id))


@teacher_bp.route("/hour-applications/<int:application_id>", methods=["GET", "POST"])
@login_required
@role_required("teacher")
def review_application_detail(application_id):
    teacher = get_current_teacher()
    if not teacher:
        flash("当前账号未绑定教师信息。", "danger")
        return redirect(url_for("teacher.dashboard"))

    application = get_teacher_application_detail(application_id, teacher.id)
    if not application:
        flash("未找到对应申请，或你无权审核。", "warning")
        return redirect(url_for("teacher.list_my_applications"))

    form = ReviewHourApplicationForm()
    is_readonly = application.status != "assigned"
    if not is_readonly and form.validate_on_submit():
        submit_review(application, teacher.id, current_user.id, form)
        flash("审核结果已提交。可点击“下一个”继续审核后续申请。", "success")
        return redirect(url_for("teacher.review_application_detail", application_id=application.id))

    if not is_readonly and form.approved_hours.data is None:
        form.approved_hours.data = application.requested_hours

    attachments = list_application_attachments(application.id)
    reviews = list_application_reviews(application.id)
    return render_template(
        "teacher/review_detail.html",
        application=application,
        attachments=attachments,
        reviews=reviews,
        form=form,
        is_readonly=is_readonly,
    )
