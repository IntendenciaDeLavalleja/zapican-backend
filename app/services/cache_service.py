"""Cache liviano sobre Redis con fallback a no-op."""
from __future__ import annotations

import json
import logging
from typing import Any

from flask import current_app

logger = logging.getLogger(__name__)


def _client():
    return current_app.extensions.get("redis") if current_app.config.get("REDIS_AVAILABLE") else None


def cache_get(key: str) -> Any:
    client = _client()
    if not client:
        return None
    try:
        raw = client.get(key)
        return json.loads(raw) if raw else None
    except Exception as exc:
        logger.debug("cache_get fallo: %s", exc)
        return None


def cache_set(key: str, value: Any, ttl: int = 300) -> None:
    client = _client()
    if not client:
        return
    try:
        client.setex(key, ttl, json.dumps(value, default=str))
    except Exception as exc:
        logger.debug("cache_set fallo: %s", exc)


def cache_clear_prefix(prefix: str) -> int:
    client = _client()
    if not client:
        return 0
    try:
        keys = list(client.scan_iter(match=f"{prefix}*"))
        if not keys:
            return 0
        client.delete(*keys)
        return len(keys)
    except Exception as exc:
        logger.debug("cache_clear_prefix fallo: %s", exc)
        return 0
