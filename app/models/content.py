"""Contenido publicable: NewsCategory, NewsPost, Event, MunicipalMeeting, CalendarItem."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.text import repair_human_text

NEWS_STATUSES = ("draft", "published", "archived")
EVENT_STATUSES = ("draft", "published", "archived")
MEETING_STATUSES = ("scheduled", "completed", "cancelled", "archived")
CALENDAR_TYPES = ("event", "meeting", "deadline", "notice", "activity")

class NewsCategory(TimestampMixin, db.Model):
    __tablename__ = "news_categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    slug: Mapped[str] = mapped_column(String(140), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(String(400))
    color: Mapped[str | None] = mapped_column(String(20))

    posts = relationship("NewsPost", back_populates="category")

    def to_public_dict(self) -> dict:
        return {"id": self.id, "name": repair_human_text(self.name), "slug": self.slug, "color": self.color}

class NewsPost(TimestampMixin, db.Model):
    __tablename__ = "news_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    slug: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    excerpt: Mapped[str | None] = mapped_column(String(600))
    content_html: Mapped[str | None] = mapped_column(Text)

    cover_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)
    og_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)

    category_id: Mapped[int | None] = mapped_column(ForeignKey("news_categories.id", ondelete="SET NULL"), nullable=True, index=True)
    author_id: Mapped[int | None] = mapped_column(ForeignKey("admin_users.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime, index=True)

    seo_title: Mapped[str | None] = mapped_column(String(240))
    seo_description: Mapped[str | None] = mapped_column(String(400))

    category = relationship("NewsCategory", back_populates="posts")
    author = relationship("AdminUser")
    cover = relationship("MediaAsset", foreign_keys=[cover_media_id])
    og_image = relationship("MediaAsset", foreign_keys=[og_media_id])

    def to_summary_dict(self) -> dict:
        return {
            "id": self.id,
            "title": repair_human_text(self.title),
            "slug": self.slug,
            "excerpt": repair_human_text(self.excerpt),
            "cover_url": self.cover.public_url if self.cover else None,
            "category": self.category.to_public_dict() if self.category else None,
            "is_featured": self.is_featured,
            "published_at": self.published_at.isoformat() if self.published_at else None,
        }

    def to_public_dict(self) -> dict:
        return {
            **self.to_summary_dict(),
            "content_html": repair_human_text(self.content_html),
            "author": self.author.full_name or self.author.username if self.author else None,
            "seo": {
                "title": repair_human_text(self.seo_title or self.title),
                "description": repair_human_text(self.seo_description or self.excerpt),
                "og_image": (self.og_image or self.cover).public_url if (self.og_image or self.cover) else None,
            },
        }

class Event(TimestampMixin, db.Model):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    slug: Mapped[str] = mapped_column(String(260), nullable=False, unique=True, index=True)
    description_html: Mapped[str | None] = mapped_column(Text)

    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime)

    location_name: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(300))
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    cover_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)
    category: Mapped[str | None] = mapped_column(String(60))

    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False, index=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)

    cover = relationship("MediaAsset", foreign_keys=[cover_media_id])

    def to_summary_dict(self) -> dict:
        return {
            "id": self.id,
            "title": repair_human_text(self.title),
            "slug": self.slug,
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "location_name": repair_human_text(self.location_name),
            "cover_url": self.cover.public_url if self.cover else None,
            "category": repair_human_text(self.category),
            "is_featured": self.is_featured,
        }

    def to_public_dict(self) -> dict:
        return {
            **self.to_summary_dict(),
            "description_html": repair_human_text(self.description_html),
            "address": repair_human_text(self.address),
            "latitude": self.latitude,
            "longitude": self.longitude,
        }

class MunicipalMeeting(TimestampMixin, db.Model):
    __tablename__ = "municipal_meetings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    meeting_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    location_name: Mapped[str | None] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(String(300))
    agenda_html: Mapped[str | None] = mapped_column(Text)
    minutes_html: Mapped[str | None] = mapped_column(Text)

    document_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False, index=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    document = relationship("MediaAsset", foreign_keys=[document_media_id])

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "title": repair_human_text(self.title),
            "description": repair_human_text(self.description),
            "meeting_datetime": self.meeting_datetime.isoformat() if self.meeting_datetime else None,
            "location_name": repair_human_text(self.location_name),
            "address": repair_human_text(self.address),
            "agenda_html": repair_human_text(self.agenda_html),
            "minutes_html": repair_human_text(self.minutes_html),
            "document_url": self.document.public_url if self.document else None,
            "status": self.status,
        }

class CalendarItem(TimestampMixin, db.Model):
    __tablename__ = "calendar_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    start_datetime: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_datetime: Mapped[datetime | None] = mapped_column(DateTime)
    type: Mapped[str] = mapped_column(String(30), default="notice", nullable=False)
    location: Mapped[str | None] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(20), default="published", nullable=False)

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "title": repair_human_text(self.title),
            "description": repair_human_text(self.description),
            "start_datetime": self.start_datetime.isoformat() if self.start_datetime else None,
            "end_datetime": self.end_datetime.isoformat() if self.end_datetime else None,
            "type": self.type,
            "location": repair_human_text(self.location),
        }
