"""CRUD Usuarios."""
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.user import AdminUser

@admin_bp.route("/users")
@login_required
def users_list():
    users = AdminUser.query.all()
    return render_template("admin/users_list.html", users=users)

@admin_bp.route("/users/new", methods=["GET", "POST"])
@login_required
def user_new():
    if request.method == "POST":
        u = AdminUser()
        u.username = (request.form.get("username") or "").strip()
        u.email = (request.form.get("email") or "").strip()
        u.full_name = (request.form.get("full_name") or "").strip() or None
        u.is_superuser = request.form.get("is_superuser") == "on"
        u.is_active = request.form.get("is_active") == "on"
        if request.form.get("password"):
            u.set_password(request.form.get("password"))
        db.session.add(u)
        db.session.commit()
        flash_ok("Usuario creado.")
        return redirect(url_for("admin.user_edit", user_id=u.id))
    return render_template("admin/user_form.html", user=None)

@admin_bp.route("/users/<int:user_id>/edit", methods=["GET", "POST"])
@login_required
def user_edit(user_id):
    u = AdminUser.query.get_or_404(user_id)
    if request.method == "POST":
        u.username = (request.form.get("username") or u.username).strip()
        u.email = (request.form.get("email") or u.email).strip()
        u.full_name = (request.form.get("full_name") or "").strip() or None
        u.is_superuser = request.form.get("is_superuser") == "on"
        u.is_active = request.form.get("is_active") == "on"
        if request.form.get("password"):
            u.set_password(request.form.get("password"))
        db.session.commit()
        flash_ok("Usuario actualizado.")
        return redirect(url_for("admin.user_edit", user_id=u.id))
    return render_template("admin/user_form.html", user=u)

@admin_bp.route("/users/<int:user_id>/delete", methods=["POST"])
@login_required
def user_delete(user_id):
    u = AdminUser.query.get_or_404(user_id)
    db.session.delete(u)
    db.session.commit()
    flash_ok("Usuario eliminado.")
    return redirect(url_for("admin.users_list"))
