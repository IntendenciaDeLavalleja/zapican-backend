"""Modelos de conf. global: SiteSettings, ThemeSettings, Authority, PageBlock."""
from __future__ import annotations
from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.extensions import db
from app.models.base import TimestampMixin
from app.utils.text import repair_human_text, repair_json_text

THEME_PRESETS = ("sierra", "campo", "patrimonio", "arroyo", "urbano", "minimal")
HEADER_VARIANTS = ("classic", "compact", "centered")
FOOTER_VARIANTS = ("standard", "minimal", "dark")
CARD_STYLES = ("soft", "outline", "elevated")
HERO_STYLES = ("image-full", "split", "minimal")
FONT_STYLES = ("inter", "lora", "merriweather", "system")

PAGE_TYPES = ("home", "tourism", "services", "custom")
BLOCK_TYPES = (
    "navigation",
    "hero", "quick_links", "featured_news", "events_preview", "meetings_preview",
    "contact_card", "map", "authorities", "tourism_highlights", "services_grid",
    "gallery", "call_to_action", "faq", "custom_text", "procedures_preview",
)

class SiteSettings(TimestampMixin, db.Model):
    __tablename__ = "site_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False, default="Mi Sitio")
    short_description: Mapped[str | None] = mapped_column(String(400))
    long_description: Mapped[str | None] = mapped_column(Text)

    logo_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)
    shield_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)
    hero_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)

    address: Mapped[str | None] = mapped_column(String(300))
    phone: Mapped[str | None] = mapped_column(String(60))
    email: Mapped[str | None] = mapped_column(String(160))
    opening_hours: Mapped[str | None] = mapped_column(String(300))

    facebook_url: Mapped[str | None] = mapped_column(String(300))
    instagram_url: Mapped[str | None] = mapped_column(String(300))
    website_url: Mapped[str | None] = mapped_column(String(300))

    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)

    seo_title: Mapped[str | None] = mapped_column(String(200))
    seo_description: Mapped[str | None] = mapped_column(String(400))
    seo_og_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)

    logo = relationship("MediaAsset", foreign_keys=[logo_media_id], post_update=True)
    shield = relationship("MediaAsset", foreign_keys=[shield_media_id], post_update=True)
    hero = relationship("MediaAsset", foreign_keys=[hero_media_id], post_update=True)
    seo_og = relationship("MediaAsset", foreign_keys=[seo_og_media_id], post_update=True)

    @classmethod
    def get_settings(cls):
        s = db.session.execute(db.select(cls).limit(1)).scalar_one_or_none()
        if not s:
            s = cls(name="Mi Sitio")
            db.session.add(s)
            db.session.commit()
        return s

    def to_public_dict(self) -> dict:
        return {
            "name": repair_human_text(self.name),
            "short_description": repair_human_text(self.short_description),
            "long_description": repair_human_text(self.long_description),
            "logo_url": self.logo.public_url if self.logo else None,
            "shield_url": self.shield.public_url if self.shield else None,
            "hero_url": self.hero.public_url if self.hero else None,
            "address": repair_human_text(self.address),
            "phone": self.phone,
            "email": self.email,
            "opening_hours": repair_human_text(self.opening_hours),
            "facebook_url": self.facebook_url,
            "instagram_url": self.instagram_url,
            "website_url": self.website_url,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "seo": {
                "title": repair_human_text(self.seo_title or self.name),
                "description": repair_human_text(self.seo_description or self.short_description),
                "og_image": self.seo_og.public_url if self.seo_og else (self.hero.public_url if self.hero else None),
            }
        }

class ThemeSettings(TimestampMixin, db.Model):
    __tablename__ = "theme_settings"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    preset: Mapped[str] = mapped_column(String(40), default="sierra", nullable=False)
    primary_color: Mapped[str] = mapped_column(String(20), default="#2f6f4e", nullable=False)
    secondary_color: Mapped[str] = mapped_column(String(20), default="#1f3a2c", nullable=False)
    accent_color: Mapped[str] = mapped_column(String(20), default="#d6a84b", nullable=False)
    background_color: Mapped[str] = mapped_column(String(20), default="#fafaf7", nullable=False)
    text_color: Mapped[str] = mapped_column(String(20), default="#1a1a1a", nullable=False)
    background_gradient_from: Mapped[str] = mapped_column(String(20), default="#f8fbf7", nullable=False)
    background_gradient_to: Mapped[str] = mapped_column(String(20), default="#eef5ef", nullable=False)
    background_gradient_angle: Mapped[int] = mapped_column(Integer, default=180, nullable=False)

    header_variant: Mapped[str] = mapped_column(String(30), default="classic", nullable=False)
    footer_variant: Mapped[str] = mapped_column(String(30), default="standard", nullable=False)
    card_style: Mapped[str] = mapped_column(String(30), default="soft", nullable=False)
    hero_style: Mapped[str] = mapped_column(String(30), default="image-full", nullable=False)
    font_style: Mapped[str] = mapped_column(String(30), default="inter", nullable=False)
    enable_dark_section: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    custom_css: Mapped[str | None] = mapped_column(Text)

    @classmethod
    def get_settings(cls):
        s = db.session.execute(db.select(cls).limit(1)).scalar_one_or_none()
        if not s:
            s = cls()
            db.session.add(s)
            db.session.commit()
        return s

    def to_public_dict(self) -> dict:
        return {
            "preset": self.preset,
            "colors": {
                "primary": self.primary_color,
                "secondary": self.secondary_color,
                "accent": self.accent_color,
                "background": self.background_color,
                "text": self.text_color,
            },
            "background_gradient": {
                "from": self.background_gradient_from,
                "to": self.background_gradient_to,
                "angle": self.background_gradient_angle,
            },
            "header_variant": self.header_variant,
            "footer_variant": self.footer_variant,
            "card_style": self.card_style,
            "hero_style": self.hero_style,
            "font_style": self.font_style,
            "enable_dark_section": self.enable_dark_section,
            "custom_css": self.custom_css,
        }

from sqlalchemy import JSON
class Authority(TimestampMixin, db.Model):
    __tablename__ = "authorities"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[str] = mapped_column(String(120), nullable=False)
    bio: Mapped[str | None] = mapped_column(Text)
    email: Mapped[str | None] = mapped_column(String(160))
    phone: Mapped[str | None] = mapped_column(String(60))
    facebook_url: Mapped[str | None] = mapped_column(String(300))
    twitter_url: Mapped[str | None] = mapped_column(String(300))
    linkedin_url: Mapped[str | None] = mapped_column(String(300))
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    photo_media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)
    photo = relationship("MediaAsset")

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "name": repair_human_text(self.name),
            "role": repair_human_text(self.role),
            "bio": repair_human_text(self.bio),
            "email": self.email,
            "phone": self.phone,
            "facebook_url": self.facebook_url,
            "twitter_url": self.twitter_url,
            "linkedin_url": self.linkedin_url,
            "order_index": self.order_index,
            "photo_url": self.photo.public_url if self.photo else None,
        }

class PageBlock(TimestampMixin, db.Model):
    __tablename__ = "page_blocks"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    page_type: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    block_type: Mapped[str] = mapped_column(String(40), nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    title: Mapped[str | None] = mapped_column(String(200))
    subtitle: Mapped[str | None] = mapped_column(String(400))
    content_html: Mapped[str | None] = mapped_column(Text)
    config_json: Mapped[dict | None] = mapped_column(JSON)
    media_id: Mapped[int | None] = mapped_column(ForeignKey("media_assets.id", ondelete="SET NULL"), nullable=True)
    media = relationship("MediaAsset")

    def to_public_dict(self) -> dict:
        return {
            "id": self.id,
            "page_type": self.page_type,
            "block_type": self.block_type,
            "display_order": self.order_index,
            "order_index": self.order_index,
            "is_active": self.is_active,
            "title": repair_human_text(self.title),
            "subtitle": repair_human_text(self.subtitle),
            "content": repair_json_text(self.config_json or {}),
            "content_html": repair_human_text(self.content_html),
            "config_json": repair_json_text(self.config_json),
            "media_url": self.media.public_url if self.media else None,
        }


