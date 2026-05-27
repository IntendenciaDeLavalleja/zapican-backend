from __future__ import annotations

import json
import secrets

from sqlalchemy import JSON, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.slug import slugify
from app.utils.text import repair_human_text, repair_json_text

PROCEDURE_SUBMISSION_STATUSES = (
    "new",
    "in_review",
    "needs_info",
    "approved",
    "rejected",
    "completed",
    "archived",
)

_TRACKING_CHARS = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # Evita chars confundibles (0/O, 1/I)


def generate_tracking_code() -> str:
    part1 = "".join(secrets.choice(_TRACKING_CHARS) for _ in range(4))
    part2 = "".join(secrets.choice(_TRACKING_CHARS) for _ in range(4))
    return f"TRM-{part1}-{part2}"


class ProcedureType(TimestampMixin, db.Model):
    __tablename__ = "procedure_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(220), nullable=False, unique=True, index=True)
    summary: Mapped[str | None] = mapped_column(String(500))
    description_html: Mapped[str | None] = mapped_column(Text)
    eligibility_notes: Mapped[str | None] = mapped_column(Text)
    fee_text: Mapped[str | None] = mapped_column(String(200))
    estimated_days: Mapped[int | None] = mapped_column(Integer)
    required_documents_json: Mapped[list | None] = mapped_column(JSON)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(db.Boolean, default=True, nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(db.Boolean, default=False, nullable=False, index=True)

    submissions = relationship(
        "ProcedureSubmission",
        back_populates="procedure_type",
        cascade="all, delete-orphan",
        order_by="desc(ProcedureSubmission.created_at)",
    )

    @property
    def required_documents(self) -> list[str]:
        raw = self.required_documents_json or []
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except Exception:
                raw = [line.strip() for line in raw.splitlines() if line.strip()]
        return [repair_human_text(str(item).strip()) for item in raw if str(item).strip()]

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "slug": self.slug,
            "title": repair_human_text(self.title),
            "summary": repair_human_text(self.summary),
            "description_html": repair_human_text(self.description_html),
            "eligibility_notes": repair_human_text(self.eligibility_notes),
            "fee_text": repair_human_text(self.fee_text),
            "estimated_days": self.estimated_days,
            "required_documents": repair_json_text(self.required_documents),
            "is_featured": self.is_featured,
            "order_index": self.order_index,
        }


class ProcedureSubmission(TimestampMixin, db.Model):
    __tablename__ = "procedure_submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    procedure_type_id: Mapped[int] = mapped_column(
        ForeignKey("procedure_types.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tracking_code: Mapped[str] = mapped_column(
        String(20), nullable=False, unique=True, index=True,
        default=generate_tracking_code,
    )
    applicant_name: Mapped[str] = mapped_column(String(160), nullable=False)
    applicant_email: Mapped[str] = mapped_column(String(160), nullable=False, index=True)
    applicant_phone: Mapped[str | None] = mapped_column(String(60))
    applicant_address: Mapped[str | None] = mapped_column(String(300))
    document_number: Mapped[str | None] = mapped_column(String(80))
    payload_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    attachments_json: Mapped[list | None] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="new", nullable=False, index=True)
    internal_notes: Mapped[str | None] = mapped_column(Text)
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)

    procedure_type = relationship("ProcedureType", back_populates="submissions")

    def to_public_receipt(self) -> dict:
        return {
            "id": self.id,
            "tracking_code": self.tracking_code,
            "status": self.status,
            "procedure": self.procedure_type.to_public_dict() if self.procedure_type else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


def procedure_document_field_name(document_name: str, index: int) -> str:
    return f"document_{index}_{slugify(document_name) or 'adjunto'}"