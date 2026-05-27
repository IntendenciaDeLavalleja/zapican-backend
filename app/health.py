"""Healthcheck simple para Docker/Coolify."""
from flask import Blueprint, current_app, jsonify

from app.extensions import db
from app.redis_utils import get_redis

health_bp = Blueprint("health", __name__)


@health_bp.route("", methods=["GET"])
@health_bp.route("/", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "lavalleja-cms"}), 200


@health_bp.route("/ready", methods=["GET"])
def ready():
    checks = {"db": False, "redis": bool(current_app.config.get("REDIS_AVAILABLE"))}
    try:
        db.session.execute(db.text("SELECT 1"))
        checks["db"] = True
    except Exception:
        pass
    status = 200 if checks["db"] else 503
    return jsonify({"status": "ready" if status == 200 else "degraded", **checks}), status
