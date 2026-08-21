from flask import Blueprint, flash, redirect, render_template, url_for
from flask_login import current_user, login_user, logout_user

from app.modules.auth.forms import LoginForm
from app.services.auth_service import authenticate_user, get_home_endpoint_by_role


auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for(get_home_endpoint_by_role(current_user.role)))

    form = LoginForm()
    if form.validate_on_submit():
        user = authenticate_user(form.username.data, form.password.data)
        if user:
            login_user(user)
            return redirect(url_for(get_home_endpoint_by_role(user.role)))
        flash("账号或密码错误，或账号已被禁用。", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("你已退出登录。", "info")
    return redirect(url_for("auth.login"))
