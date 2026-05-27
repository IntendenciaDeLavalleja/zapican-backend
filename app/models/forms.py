"""Formularios personalizados: CustomForm, FormField, ContactMessage, FormSubmission."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.text import repair_human_text

FIELD_TYPES = ("text", "email", "number", "textarea", "select", "checkbox", "date", "file")
FORM_SUBMISSION_STATUSES = ("new", "reviewed", "archived")

class CustomForm(TimestampMixin, db.Model):
    __tablename__ = "custom_forms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notify_emails: Mapped[str | None] = mapped_column(String(500))

    fields = relationship("FormField", back_populates="form", cascade="all, delete-orphan", order_by="FormField.order_index")
    submissions = relationship("FormSubmission", back_populates="form", cascade="all, delete-orphan")

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "title": repair_human_text(self.title),
            "slug": self.slug,
            "description": repair_human_text(self.description),
            "fields": [f.to_dict() for f in self.fields if f.is_active],
        }

class FormField(db.Model):
    __tablename__ = "form_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("custom_forms.id", ondelete="CASCADE"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    field_type: Mapped[str] = mapped_column(String(30), default="text", nullable=False)
    is_required: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    options: Mapped[str | None] = mapped_column(Text)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    form = relationship("CustomForm", back_populates="fields")

    def to_dict(self) -> dict:
        opts = [o.strip() for o in self.options.split(",")] if self.options else []
        return {
            "id": self.id,
            "name": self.name,
            "label": repair_human_text(self.label),
            "type": self.field_type,
            "required": self.is_required,
            "options": [repair_human_text(option) for option in opts],
        }

class FormSubmission(TimestampMixin, db.Model):
    __tablename__ = "form_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    form_id: Mapped[int] = mapped_column(ForeignKey("custom_forms.id", ondelete="CASCADE"), nullable=False, index=True)
    data_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False, index=True)
    internal_notes: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    form = relationship("CustomForm", back_populates="submissions")

class ContactMessage(TimestampMixin, db.Model):
    __tablename__ = "contact_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    email: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(60))
    subject: Mapped[str | None] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    ip_address: Mapped[str | None] = mapped_column(String(45))
