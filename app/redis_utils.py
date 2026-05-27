"""Probe Redis con fallback graceful."""
from __future__ import annotations

import logging

import redis

logger = logging.getLogger(__name__)


def init_redis(app) -> bool:
    url = app.config.get("REDIS_URL", "")
    if not url:
        app.config["REDIS_AVAILABLE"] = False
        return False
    try:
        client = redis.Redis.from_url(url, socket_connect_timeout=2, socket_timeout=2)
        client.ping()
        app.config["REDIS_AVAILABLE"] = True
        app.extensions["redis"] = client
        return True
    except Exception as exc:
        logger.warning("Redis no disponible (%s). Continuamos sin cache distribuido.", exc)
        app.config["REDIS_AVAILABLE"] = False
        return False


def get_redis(app):
    return app.extensions.get("redis") if app.config.get("REDIS_AVAILABLE") else None
