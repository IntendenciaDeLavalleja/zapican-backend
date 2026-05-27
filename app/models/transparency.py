"""Solicitudes de acceso a la información pública (Transparencia)."""
from __future__ import annotations

from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db
from app.models.base import TimestampMixin

TRANSPARENCY_REQUEST_STATUSES = ("new", "in_review", "answered", "archived")


class TransparencyRequest(TimestampMixin, db.Model):
    __tablename__ = "transparency_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    reference_number: Mapped[str] = mapped_column(String(20), nullable=False, unique=True, index=True)

    requester_type: Mapped[str] = mapped_column(String(60), nullable=False)
    full_name: Mapped[str] = mapped_column(String(220), nullable=False)
    identifier: Mapped[str] = mapped_column(String(100), nullable=False)
    address: Mapped[str] = mapped_column(String(300), nullable=False)
    email: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(60))

    preferred_response_channel: Mapped[str] = mapped_column(String(80), nullable=False)
    requested_information: Mapped[str] = mapped_column(Text, nullable=False)
    additional_location_data: Mapped[str | None] = mapped_column(Text)
    preferred_format: Mapped[str | None] = mapped_column(String(80))
    municipality: Mapped[str] = mapped_column(String(160), nullable=False)
    accepted_terms: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False, index=True)
    internal_notes: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reference_number": self.reference_number,
            "requester_type": self.requester_type,
            "full_name": self.full_name,
            "identifier": self.identifier,
            "address": self.address,
            "email": self.email,
            "phone": self.phone,
            "preferred_response_channel": self.preferred_response_channel,
            "requested_information": self.requested_information,
            "additional_location_data": self.additional_location_data,
            "preferred_format": self.preferred_format,
            "municipality": self.municipality,
            "accepted_terms": self.accepted_terms,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
