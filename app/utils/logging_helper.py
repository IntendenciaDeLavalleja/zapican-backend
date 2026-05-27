"""Helper para registrar acciones administrativas en AuditLog."""
from __future__ import annotations

import logging

from flask import has_request_context, request

logger = logging.getLogger(__name__)


def log_activity(action: str, *, entity_type: str | None = None, entity_id=None,
                 details: str | None = None, municipality_id=None,
                 old_values=None, new_values=None, user=None):
    """Crea un AuditLog tolerante a fallos."""
    from app.extensions import db
    from app.models.user import AuditLog

    try:
        user_id = None
        if user is None and has_request_context():
            try:
                from flask_login import current_user
                if current_user and current_user.is_authenticated:
                    user = current_user
            except Exception:
                user = None
        if user is not None:
            user_id = getattr(user, "id", None)
        ip = None
        ua = None
        if has_request_context():
            ip = (request.headers.get("X-Forwarded-For") or request.remote_addr or "")[:45]
            ua = (request.headers.get("User-Agent") or "")[:500]
        log = AuditLog(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            details=details,
            old_values_json=old_values,
            new_values_json=new_values,
            ip_address=ip,
            user_agent=ua,
        )
        db.session.add(log)
        db.session.commit()
    except Exception as exc:
        logger.warning("log_activity fallo: %s", exc)
        try:
            db.session.rollback()
        except Exception:
            pass
