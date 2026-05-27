"""Autenticacion administrativa."""
import random
from flask import redirect, render_template, request, url_for, session
from flask_login import login_required, login_user, logout_user, current_user
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.models.user import AdminUser
from app.utils.logging_helper import log_activity


@admin_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        login_id = request.form.get("email") or request.form.get("username")
        password = request.form.get("password")
        captcha_ans = request.form.get("captcha", "")

        expected_captcha = session.get("login_captcha")

        if (
            not expected_captcha
            or not captcha_ans.isdigit()
            or int(captcha_ans) != expected_captcha
        ):
            log_activity(
                "AUTH_LOGIN_FAILED",
                entity_type="auth",
                details=f"captcha invalido para {login_id or 'desconocido'}",
            )
            flash_err(
                "La verificación anti-spam (suma espacial) es incorrecta.",
            )
        else:
            u = AdminUser.query.filter(
                (AdminUser.username == login_id)
                | (AdminUser.email == login_id)
            ).first()
            if u and u.is_active and u.check_password(password):
                session.pop("login_captcha", None)
                login_user(u)
                log_activity(
                    "AUTH_LOGIN",
                    entity_type="auth",
                    details=f"inicio de sesion: {u.username}",
                    user=u,
                )
                flash_ok("Bienvenido/a de nuevo.")
                return redirect(url_for("admin.dashboard"))
            log_activity(
                "AUTH_LOGIN_FAILED",
                entity_type="auth",
                details=(
                    f"credenciales invalidas para {login_id or 'desconocido'}"
                ),
                user=u,
            )
            flash_err("Credenciales invalidas o usuario inactivo.")

    a = random.randint(1, 9)
    b = random.randint(1, 9)
    session["login_captcha"] = a + b
    captcha_question = f"{a} + {b}"

    return render_template(
        "admin/login.html",
        captcha_question=captcha_question,
    )


@admin_bp.route("/logout")
@login_required
def logout():
    log_activity(
        "AUTH_LOGOUT",
        entity_type="auth",
        details=f"cierre de sesion: {current_user.username}",
        user=current_user,
    )
    logout_user()
    return redirect(url_for("admin.login"))
