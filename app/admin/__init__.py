"""Blueprint del panel administrativo."""
from flask import Blueprint, current_app, request

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")

_AUDITED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@admin_bp.after_request
def _audit_admin_mutations(response):
    endpoint = request.endpoint or ""
    if response.status_code >= 400:
        return response
    if request.method not in _AUDITED_METHODS:
        return response
    if not endpoint.startswith("admin.") or endpoint == "admin.login":
        return response

    try:
        from flask_login import current_user

        from app.utils.logging_helper import log_activity

        actor = None
        if getattr(current_user, "is_authenticated", False):
            actor = current_user
        action_name = endpoint.split(".", 1)[1].upper()
        details = request.full_path.rstrip("?")
        log_activity(
            f"ADMIN_{request.method}_{action_name}",
            entity_type=endpoint,
            details=details,
            user=actor,
        )
    except Exception as exc:
        current_app.logger.warning("audit admin mutation failed: %s", exc)

    return response

from app.admin.routes_components import (  # noqa: E402,F401
    auth as _auth,
    dashboard as _dashboard,
    settings as _settings,
    news as _news,
    events as _events,
    meetings as _meetings,
    calendar as _calendar,
    forms as _forms,
    procedures as _procedures,
    contact as _contact,
    authorities as _authorities,
    blocks as _blocks,
    media as _media,
    audit as _audit,
    users as _users,
    quick_links as _quick_links,
    novedades_settings as _novedades_settings,
    transparency as _transparency,
)


@admin_bp.context_processor
def _inject_contact_count():
    try:
        from app.models.forms import ContactMessage
        count = ContactMessage.query.filter_by(is_read=False).count()
    except Exception:
        count = 0
    try:
        from app.models.procedures import ProcedureSubmission
        new_proc = ProcedureSubmission.query.filter_by(status="new").count()
    except Exception:
        new_proc = 0
    try:
        from app.models.transparency import TransparencyRequest

        new_transparency = TransparencyRequest.query.filter_by(
            is_read=False,
        ).count()
    except Exception:
        new_transparency = 0
    return {
        "unread_contact_count": count,
        "new_procedure_count": new_proc,
        "new_transparency_count": new_transparency,
    }
