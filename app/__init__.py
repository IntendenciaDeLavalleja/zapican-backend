"""App factory."""
from __future__ import annotations

import logging
import os
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, jsonify, send_from_directory

from app.config import Config
from app.extensions import (
    cache,
    cors,
    csrf,
    db,
    init_limiter,
    login_manager,
    mail,
    migrate,
    talisman,
)
from app.redis_utils import init_redis

load_dotenv()


def create_app(config_class: type[Config] = Config) -> Flask:
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object(config_class)
    public_dir = Path(app.root_path).parent / "public"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )

    init_redis(app)

    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    cache.init_app(
        app,
        config={
            "CACHE_TYPE": "RedisCache" if app.config.get("REDIS_AVAILABLE") else "SimpleCache",
            "CACHE_REDIS_URL": app.config.get("REDIS_URL"),
            "CACHE_DEFAULT_TIMEOUT": 300,
        },
    )
    cors.init_app(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get("CORS_ALLOWED_ORIGINS", []),
                "supports_credentials": False,
            }
        },
    )
    if app.config.get("TALISMAN_FORCE_HTTPS"):
        talisman.init_app(
            app,
            content_security_policy=None,  # CSP fino se hace en nginx
            force_https=True,
        )

    init_limiter(app)

    # MinIO
    from app.services.minio_service import minio_service
    minio_service.init_app(app)

    # Login manager
    login_manager.login_view = "admin.login"
    login_manager.login_message = "Iniciá sesión para continuar."
    login_manager.login_message_category = "warning"

    @login_manager.user_loader
    def _load_user(user_id):
        from app.models.user import AdminUser
        return AdminUser.query.get(int(user_id)) if user_id else None

    # Métricas
    from app.metrics import metrics_bp, register_request_hooks
    register_request_hooks(app)
    app.register_blueprint(metrics_bp, url_prefix="/metrics")
    csrf.exempt(metrics_bp)

    # Health
    from app.health import health_bp
    app.register_blueprint(health_bp, url_prefix="/health")
    csrf.exempt(health_bp)

    # API pública
    from app.api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api/v1")
    csrf.exempt(api_bp)

    # Admin
    from app.admin import admin_bp
    app.register_blueprint(admin_bp, url_prefix="/admin")

    # Comandos CLI
    from app.commands import register_cli
    register_cli(app)

    @app.get("/favicon.ico")
    def favicon():
        return send_from_directory(public_dir, "favicon.ico")

    # Handlers
    from flask import request, jsonify, flash, redirect, render_template
    from flask_wtf.csrf import CSRFError

    @app.errorhandler(CSRFError)
    def handle_csrf_error(e):
        if request.path.startswith(("/admin",)):
            flash("El formulario expiró por seguridad. Por favor, refresca la página e intenta de nuevo.", "error")
            return redirect(request.referrer or request.url)
        return jsonify({"error": "csrf_token_expired", "message": "El código de seguridad del formulario ha vencido. Intente nuevamente."}), 400

    @app.errorhandler(404)
    def _not_found(_):
        if request.path.startswith(("/api", "/health", "/metrics")):
            return jsonify({"error": "not_found"}), 404
        return render_template("404.html"), 404

    @app.errorhandler(500)
    def _server_error(_):
        return jsonify({"error": "internal_error"}), 500

    @app.route("/")
    def _root():
        return render_template("404.html"), 404

    return app
