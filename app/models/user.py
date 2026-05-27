"""Usuarios admin, 2FA y AuditLog."""
from __future__ import annotations

from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask_login import UserMixin
from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin

_hasher = PasswordHasher()

class AdminUser(UserMixin, TimestampMixin, db.Model):
    __tablename__ = "admin_users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(160), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(160))

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime)

    two_factor_codes = relationship("TwoFactorCode", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        self.password_hash = _hasher.hash(password)

    def check_password(self, password: str) -> bool:
        try:
            return _hasher.verify(self.password_hash, password)
        except (VerifyMismatchError, Exception):
            return False

    def can_manage(self) -> bool:
        return self.is_superuser or self.is_active

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "full_name": self.full_name,
            "is_active": self.is_active,
            "is_superuser": self.is_superuser,
        }

class TwoFactorCode(db.Model):
    __tablename__ = "two_factor_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("AdminUser", back_populates="two_factor_codes")

    @classmethod
    def issue(cls, user: "AdminUser", code: str, ttl_minutes: int = 10) -> "TwoFactorCode":
        instance = cls(
            user_id=user.id,
            code_hash=_hasher.hash(code),
            expires_at=datetime.utcnow() + timedelta(minutes=ttl_minutes),
        )
        return instance

    def verify(self, code: str) -> bool:
        if self.consumed_at is not None:
            return False
        if datetime.utcnow() > self.expires_at:
            return False
        try:
            return _hasher.verify(self.code_hash, code)
        except (VerifyMismatchError, Exception):
            return False

class AuditLog(db.Model):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(80), nullable=False, index=True)
    entity_type: Mapped[str | None] = mapped_column(String(80), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(80))
    details: Mapped[str | None] = mapped_column(Text)
    old_values_json: Mapped[dict | None] = mapped_column(JSON)
    new_values_json: Mapped[dict | None] = mapped_column(JSON)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    user = relationship("AdminUser")
