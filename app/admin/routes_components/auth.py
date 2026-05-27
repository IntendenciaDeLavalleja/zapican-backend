"""Autenticacion administrativa."""
from datetime import datetime
import random
import secrets

from flask import (
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_login import login_required, login_user, logout_user, current_user
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db, get_limiter
from app.models.user import AdminUser, TwoFactorCode
from app.services.email_service import send_2fa_code
from app.utils.logging_helper import log_activity


@admin_bp.route("/login", methods=["GET", "POST"])
@get_limiter().limit("5 per minute")
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
                session["2fa_user_id"] = u.id
                code = "".join(secrets.choice("0123456789") for _ in range(6))
                ttl_minutes = current_app.config.get(
                    "TWOFA_CODE_TTL_MINUTES",
                    10,
                )
                db.session.add(
                    TwoFactorCode.issue(u, code, ttl_minutes=ttl_minutes),
                )
                db.session.commit()
                send_2fa_code(u.email, code)
                log_activity(
                    "AUTH_LOGIN_STEP1_SUCCESS",
                    entity_type="auth",
                    details=f"codigo 2FA enviado a {u.email}",
                    user=u,
                )
                return redirect(url_for("admin.verify_2fa"))
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


@admin_bp.route("/verify-2fa", methods=["GET", "POST"])
@get_limiter().limit("5 per minute")
def verify_2fa():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    user_id = session.get("2fa_user_id")
    if not user_id:
        return redirect(url_for("admin.login"))

    user = AdminUser.query.get(user_id)
    if not user or not user.is_active:
        session.pop("2fa_user_id", None)
        flash_err("La verificación expiró. Iniciá sesión nuevamente.")
        return redirect(url_for("admin.login"))

    if request.method == "POST":
        code = (request.form.get("code") or "").strip()

        if not code:
            flash_err("Ingresá el código de verificación.")
            return render_template("admin/verify_2fa.html")

        if not code.isdigit() or len(code) != 6:
            flash_err("El código debe tener 6 dígitos numéricos.")
            return render_template("admin/verify_2fa.html")

        tf_code = (
            TwoFactorCode.query.filter_by(user_id=user.id, consumed_at=None)
            .order_by(TwoFactorCode.created_at.desc())
            .first()
        )

        if tf_code and tf_code.verify(code):
            tf_code.consumed_at = datetime.utcnow()
            db.session.commit()
            login_user(user)
            session.pop("2fa_user_id", None)
            log_activity(
                "AUTH_LOGIN_2FA_SUCCESS",
                entity_type="auth",
                details=f"inicio de sesion: {user.username}",
                user=user,
            )
            flash_ok("Bienvenido/a de nuevo.")
            return redirect(url_for("admin.dashboard"))

        log_activity(
            "AUTH_LOGIN_2FA_FAILED",
            entity_type="auth",
            details=f"codigo 2FA invalido para usuario ID: {user_id}",
            user=user,
        )
        flash_err("Código inválido o expirado.")

    return render_template("admin/verify_2fa.html")


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
