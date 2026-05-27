"""Extensiones Flask compartidas."""
from __future__ import annotations

import logging

from flask_caching import Cache
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_mail import Mail
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect

logger = logging.getLogger(__name__)

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
csrf = CSRFProtect()
login_manager = LoginManager()
cors = CORS()
talisman = Talisman()
cache = Cache()

# El limiter se construye lazy en init_limiter porque su storage_uri depende de config.
limiter: Limiter | None = None


def init_limiter(app):
    """Inicializa Flask-Limiter con fallback a memory:// si Redis falla."""
    global limiter
    storage_uri = app.config.get("RATELIMIT_STORAGE_URI") or "memory://"
    try:
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri=storage_uri,
            default_limits=[app.config.get("RATELIMIT_DEFAULT", "200/minute")],
            headers_enabled=True,
        )
        limiter.init_app(app)
    except Exception as exc:  # pragma: no cover
        logger.warning("Limiter con Redis fallo (%s). Usando memory://", exc)
        limiter = Limiter(
            key_func=get_remote_address,
            storage_uri="memory://",
            default_limits=[app.config.get("RATELIMIT_DEFAULT", "200/minute")],
            headers_enabled=True,
        )
        limiter.init_app(app)
    return limiter


def get_limiter() -> Limiter:
    if limiter is None:
        raise RuntimeError("Limiter no inicializado todavia")
    return limiter
