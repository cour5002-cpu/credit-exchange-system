from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.modules.hour_application.forms import AssignTeacherForm
from app.services.form_option_service import get_test_course_map, get_test_major_options
from app.services.hour_application_service import (
    assign_teacher,
    get_application_by_id,
    get_filtered_teacher_choices,
    list_application_attachments,
    list_application_reviews,
    list_all_applications,
)
from app.utils.permissions import role_required


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@role_required("admin")
def dashboard():
    return render_template("admin/dashboard.html")


@admin_bp.route("/hour-applications")
@login_required
@role_required("admin")
def list_hour_applications():
    status = request.args.get("status") or None
    applications = list_all_applications(status=status)
    return render_template(
        "admin/hour_application_list.html",
        applications=applications,
        current_status=status or "",
    )


@admin_bp.route("/hour-applications/<int:application_id>")
@login_required
@role_required("admin")
def hour_application_detail(application_id):
    application = get_application_by_id(application_id)
    if not application:
        flash("未找到对应申请。", "warning")
        return redirect(url_for("admin.list_hour_applications"))

    attachments = list_application_attachments(application.id)
    reviews = list_application_reviews(application.id)
    return render_template(
        "admin/hour_application_detail.html",
        application=application,
        attachments=attachments,
        reviews=reviews,
    )


@admin_bp.route("/hour-applications/<int:application_id>/assign", methods=["GET", "POST"])
@login_required
@role_required("admin")
def assign_hour_application_teacher(application_id):
    application = get_application_by_id(application_id)
    if not application:
        flash("未找到对应申请。", "warning")
        return redirect(url_for("admin.list_hour_applications"))

    major_name = request.args.get("major_name", "")
    course_name = request.args.get("course_name", "")
    keyword = request.args.get("keyword", "")

    form = AssignTeacherForm()
    form.teacher_id.choices = get_filtered_teacher_choices(
        major_name=major_name,
        course_name=course_name,
        keyword=keyword,
    )

    if form.validate_on_submit():
        try:
            # 将教师ID字符串转换为整数
            teacher_id = int(form.teacher_id.data)
            assign_teacher(application, teacher_id)
            flash("审核教师分配成功。", "success")
            return redirect(url_for("admin.list_hour_applications"))
        except ValueError:
            flash("请选择有效的教师。", "danger")
        except Exception as e:
            flash(f"分配失败，请稍后重试。错误信息：{str(e)}", "danger")

    return render_template(
        "admin/assign_teacher.html",
        application=application,
        form=form,
        major_name=major_name,
        course_name=course_name,
        keyword=keyword,
        major_options=get_test_major_options(),
        course_options=sorted({course for values in get_test_course_map().values() for course in values}),
    )
