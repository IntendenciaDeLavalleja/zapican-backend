"""Configuración Flask por variables de entorno."""
from __future__ import annotations

import os
from datetime import timedelta

from sqlalchemy.engine import make_url


def _bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on", "y"}


def _csv(value: str | None) -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(",") if v.strip()]


def _database_url() -> str:
    url = (
        os.getenv("DATABASE_URI")
        or os.getenv("DATABASE_URL")
        or (
            "mariadb+mariadbconnector://"
            "lavalleja:lavalleja@localhost:3306/lavalleja_cms"
        )
    )
    if url.startswith("mysql+mariadbconnector://"):
        url = (
            "mariadb+mariadbconnector://"
            + url.removeprefix("mysql+mariadbconnector://")
        )
    # mariadb-connector-python does not accept charset= as a URL query param;
    # charset is enforced via init_command in SQLALCHEMY_ENGINE_OPTIONS instead.
    if url.startswith("mariadb+mariadbconnector://") and "charset=" in url:
        parsed = make_url(url)
        query = dict(parsed.query)
        query.pop("charset", None)
        url = parsed.set(query=query).render_as_string(hide_password=False)
    return url


class Config:
    # --- Flask ---
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    WTF_CSRF_SECRET_KEY = os.getenv("WTF_CSRF_SECRET_KEY", SECRET_KEY)
    WTF_CSRF_TIME_LIMIT = int(os.getenv("WTF_CSRF_TIME_LIMIT", "3600"))
    PERMANENT_SESSION_LIFETIME = timedelta(
        hours=int(os.getenv("SESSION_LIFETIME_HOURS", "8"))
    )
    JSON_SORT_KEYS = False
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_MB", "20")) * 1024 * 1024

    # --- DB ---
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        # Explicitly set charset on every new connection.
        # mariadb-connector-python does not support a 'charset' URL param or kwarg;
        # init_command is the supported mechanism to guarantee utf8mb4 at the
        # session level regardless of server defaults or connector version.
        "connect_args": {"init_command": "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci"},
    }

    # --- Redis ---
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

    # --- Mail ---
    MAIL_SERVER = os.getenv("MAIL_SERVER", "")
    MAIL_PORT = int(os.getenv("MAIL_PORT", "587"))
    MAIL_USERNAME = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD", "")
    MAIL_USE_TLS = _bool(os.getenv("MAIL_USE_TLS"), True)
    MAIL_USE_SSL = _bool(os.getenv("MAIL_USE_SSL"), False)
    MAIL_DEFAULT_SENDER = os.getenv(
        "MAIL_DEFAULT_SENDER",
        "Intendencia de Lavalleja <no-reply@lavalleja.example>",
    )

    # --- MinIO ---
    MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "")
    MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "")
    MINIO_BUCKET = os.getenv(
        "MINIO_BUCKET",
        os.getenv("MINIO_BUCKET_NAME", "lavalleja-cms"),
    )
    MINIO_SECURE = _bool(os.getenv("MINIO_SECURE"), False)
    MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "").rstrip("/")

    # --- CORS / Front ---
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:4321")
    CORS_ALLOWED_ORIGINS = _csv(os.getenv("CORS_ORIGINS")) or [FRONTEND_URL]

    # --- Rate limit ---
    RATELIMIT_STORAGE_URI = REDIS_URL
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200/minute")
    RATELIMIT_HEADERS_ENABLED = True

    # --- Talisman ---
    TALISMAN_FORCE_HTTPS = _bool(os.getenv("TALISMAN_FORCE_HTTPS"), False)

    # --- 2FA ---
    TWOFA_CODE_TTL_MINUTES = int(os.getenv("TWOFA_CODE_TTL_MINUTES", "10"))

    # --- Bootstrap admin ---
    ADMIN_BOOTSTRAP_USERNAME = os.getenv("ADMIN_BOOTSTRAP_USERNAME", "admin")
    ADMIN_BOOTSTRAP_EMAIL = os.getenv(
        "ADMIN_BOOTSTRAP_EMAIL",
        "admin@lavalleja.example",
    )
    ADMIN_BOOTSTRAP_PASSWORD = os.getenv("ADMIN_BOOTSTRAP_PASSWORD", "")

    # --- Uploads ---
    UPLOAD_ALLOWED_IMAGE_MIMES = {"image/webp", "image/jpeg", "image/png"}
    UPLOAD_ALLOWED_DOC_MIMES = {"application/pdf"}
    UPLOAD_MAX_IMAGE_BYTES = 8 * 1024 * 1024
    UPLOAD_MAX_DOC_BYTES = 16 * 1024 * 1024
