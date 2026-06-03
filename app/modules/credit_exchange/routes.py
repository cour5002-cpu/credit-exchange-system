from decimal import Decimal

from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_required

from app.models.student_hour_account import StudentHourAccount
from app.modules.credit_exchange.forms import (
    CreditExchangeApplicationForm,
    CreditExchangeReviewForm,
)
from app.services.config_service import get_credit_exchange_ratio
from app.services.credit_exchange_service import (
    calculate_estimated_credits,
    create_credit_exchange_application,
    get_credit_exchange_detail_for_admin,
    get_credit_exchange_detail_for_student,
    list_credit_exchange_applications_for_admin,
    list_credit_exchange_applications_for_student,
    submit_credit_exchange_review,
)
from app.services.student_service import get_current_student
from app.utils.permissions import role_required


credit_exchange_bp = Blueprint(
    "credit_exchange",
    __name__,
    url_prefix="/credit-exchanges",
)


@credit_exchange_bp.route("/new", methods=["GET", "POST"])
@login_required
@role_required("student")
def create_application():
    student = get_current_student()
    if not student:
        flash("当前账号未绑定学生信息。", "danger")
        return redirect(url_for("student.dashboard"))

    account = StudentHourAccount.query.filter_by(student_id=student.id).first()
    available_hours = Decimal(str(account.available_hours if account else 0))

    form = CreditExchangeApplicationForm()
    estimated_credits = Decimal("0.00")
    if form.requested_hours.data:
        estimated_credits = calculate_estimated_credits(form.requested_hours.data)

    if form.validate_on_submit():
        try:
            create_credit_exchange_application(
                student_id=student.id,
                requested_hours=form.requested_hours.data,
                description=form.description.data,
            )
            flash("学分兑换申请已提交。", "success")
            return redirect(url_for("credit_exchange.student_list"))
        except ValueError as exc:
            form.requested_hours.errors.append(str(exc))
        except Exception as e:
            # 捕获所有其他异常（数据库错误、网络错误等）
            flash(f"提交失败，请稍后重试。错误信息：{str(e)}", "danger")

    return render_template(
        "student/credit_exchange_create.html",
        form=form,
        available_hours=available_hours,
        estimated_credits=estimated_credits,
        credit_exchange_ratio=get_credit_exchange_ratio(),
    )


@credit_exchange_bp.route("")
@login_required
@role_required("student")
def student_list():
    student = get_current_student()
    if not student:
        flash("当前账号未绑定学生信息。", "danger")
        return redirect(url_for("student.dashboard"))

    applications = list_credit_exchange_applications_for_student(student.id)
    return render_template("student/credit_exchange_list.html", applications=applications)


@credit_exchange_bp.route("/<int:application_id>")
@login_required
@role_required("student")
def student_detail(application_id):
    student = get_current_student()
    if not student:
        flash("当前账号未绑定学生信息。", "danger")
        return redirect(url_for("student.dashboard"))

    application = get_credit_exchange_detail_for_student(student.id, application_id)
    if not application:
        flash("未找到对应兑换申请。", "warning")
        return redirect(url_for("credit_exchange.student_list"))

    return render_template("student/credit_exchange_detail.html", application=application)


@credit_exchange_bp.route("/admin")
@login_required
@role_required("admin")
def admin_list():
    applications = list_credit_exchange_applications_for_admin()
    return render_template("admin/credit_exchange_list.html", applications=applications)


@credit_exchange_bp.route("/admin/<int:application_id>", methods=["GET", "POST"])
@login_required
@role_required("admin")
def admin_detail(application_id):
    application = get_credit_exchange_detail_for_admin(application_id)
    if not application:
        flash("未找到对应兑换申请。", "warning")
        return redirect(url_for("credit_exchange.admin_list"))

    form = CreditExchangeReviewForm()
    if form.validate_on_submit():
        try:
            submit_credit_exchange_review(
                application=application,
                action=form.action.data,
                review_comment=form.review_comment.data,
                admin_user_id=current_user.id,
            )
            flash("兑换申请审核完成。", "success")
            return redirect(url_for("credit_exchange.admin_list"))
        except ValueError as exc:
            flash(str(exc), "danger")
        except Exception as e:
            # 捕获所有其他异常（数据库错误、网络错误等）
            flash(f"审核失败，请稍后重试。错误信息：{str(e)}", "danger")

    return render_template(
        "admin/credit_exchange_detail.html",
        application=application,
        form=form,
    )
