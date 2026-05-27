"""Visor de logs de auditoria."""

from flask import render_template, request
from flask_login import login_required
from app.admin import admin_bp
from app.models.user import AdminUser, AuditLog


@admin_bp.route("/audit")
@login_required
def audit_list():
    query = AuditLog.query

    user_id = (request.args.get("user_id") or "").strip()
    entity_type = (request.args.get("entity_type") or "").strip()

    if user_id.isdigit():
        query = query.filter(AuditLog.user_id == int(user_id))
    if entity_type:
        query = query.filter(AuditLog.entity_type.ilike(f"%{entity_type}%"))

    logs = query.order_by(AuditLog.created_at.desc()).limit(200).all()
    users = AdminUser.query.order_by(AdminUser.username.asc()).all()
    return render_template("admin/audit_list.html", logs=logs, users=users)
