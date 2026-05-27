"""Configuracion Global y Temas."""

from flask import redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_ok
from app.extensions import db
from app.models.media import MediaAsset
from app.models.settings import (
    CARD_STYLES,
    FONT_STYLES,
    FOOTER_VARIANTS,
    HEADER_VARIANTS,
    HERO_STYLES,
    THEME_PRESETS,
    PageBlock,
    SiteSettings,
    ThemeSettings,
)

THEME_PRESET_VALUES = {
    "sierra": {
        "primary_color": "#3a6ea5",
        "secondary_color": "#1f3850",
        "accent_color": "#f5b13d",
        "background_color": "#f3f7fb",
        "text_color": "#0f172a",
        "background_gradient_from": "#eff6ff",
        "background_gradient_to": "#e8eef9",
        "background_gradient_angle": 180,
    },
    "campo": {
        "primary_color": "#2f6f4e",
        "secondary_color": "#1f3a2c",
        "accent_color": "#d6a84b",
        "background_color": "#fafaf7",
        "text_color": "#1a1a1a",
        "background_gradient_from": "#f8fbf7",
        "background_gradient_to": "#eef5ef",
        "background_gradient_angle": 180,
    },
    "patrimonio": {
        "primary_color": "#7a4a2f",
        "secondary_color": "#3b251a",
        "accent_color": "#c9a66b",
        "background_color": "#faf6f1",
        "text_color": "#1f2937",
        "background_gradient_from": "#fbf5ee",
        "background_gradient_to": "#f0e2d2",
        "background_gradient_angle": 180,
    },
    "arroyo": {
        "primary_color": "#1f7a8c",
        "secondary_color": "#0f3b46",
        "accent_color": "#f5d76e",
        "background_color": "#f2fbfd",
        "text_color": "#102a43",
        "background_gradient_from": "#effbfd",
        "background_gradient_to": "#e3f4f7",
        "background_gradient_angle": 180,
    },
    "urbano": {
        "primary_color": "#1f2937",
        "secondary_color": "#0f172a",
        "accent_color": "#f59e0b",
        "background_color": "#f8fafc",
        "text_color": "#111827",
        "background_gradient_from": "#f8fafc",
        "background_gradient_to": "#edf2f7",
        "background_gradient_angle": 180,
    },
    "minimal": {
        "primary_color": "#111827",
        "secondary_color": "#374151",
        "accent_color": "#3b82f6",
        "background_color": "#ffffff",
        "text_color": "#111827",
        "background_gradient_from": "#ffffff",
        "background_gradient_to": "#f3f4f6",
        "background_gradient_angle": 180,
    },
}


def _get_or_create_home_hero_block() -> PageBlock:
    block = (
        PageBlock.query
        .filter_by(page_type="home", block_type="hero")
        .order_by(PageBlock.order_index.asc(), PageBlock.id.asc())
        .first()
    )
    if block:
        return block

    block = PageBlock(
        page_type="home",
        block_type="hero",
        title="",
        subtitle="",
        is_active=True,
        config_json={},
    )
    db.session.add(block)
    db.session.commit()
    return block


def _optional_float(value: str | None) -> float | None:
    if not value:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _optional_int(value: str | None) -> int | None:
    if not value:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


@admin_bp.route("/settings/site", methods=["GET", "POST"])
@login_required
def site_settings():
    s = SiteSettings.get_settings()
    if request.method == "POST":
        s.name = request.form.get("name") or "Mi Sitio"
        s.short_description = request.form.get("short_description")
        s.long_description = request.form.get("long_description")
        s.address = request.form.get("address")
        s.phone = request.form.get("phone")
        s.email = request.form.get("email")
        s.opening_hours = request.form.get("opening_hours")
        s.facebook_url = request.form.get("facebook_url")
        s.instagram_url = request.form.get("instagram_url")
        s.website_url = request.form.get("website_url")
        s.latitude = _optional_float(request.form.get("latitude"))
        s.longitude = _optional_float(request.form.get("longitude"))
        s.seo_title = request.form.get("seo_title")
        s.seo_description = request.form.get("seo_description")

        s.logo_media_id = _optional_int(request.form.get("logo_media_id"))
        s.shield_media_id = _optional_int(request.form.get("shield_media_id"))
        s.hero_media_id = _optional_int(request.form.get("hero_media_id"))

        db.session.commit()
        flash_ok("Configuración del sitio guardada.")
        return redirect(url_for("admin.site_settings"))

    media_assets = (
        MediaAsset.query
        .filter(MediaAsset.mime_type.like("image/%"))
        .order_by(MediaAsset.created_at.desc())
        .all()
    )
    return render_template("admin/site_form.html", site=s, media_assets=media_assets)


@admin_bp.route("/settings/home-hero", methods=["GET", "POST"])
@login_required
def home_hero_settings():
    site = SiteSettings.get_settings()
    hero_block = _get_or_create_home_hero_block()
    hero_config = hero_block.config_json or {}

    if request.method == "POST":
        hero_block.title = request.form.get("title") or None
        hero_block.subtitle = request.form.get("subtitle") or None
        hero_block.is_active = request.form.get("is_active") == "on"

        site.hero_media_id = _optional_int(request.form.get("hero_media_id"))

        site.opening_hours = request.form.get("opening_hours") or None

        hero_block.config_json = {
            "badge_text": request.form.get("badge_text") or None,
            "eyebrow": request.form.get("eyebrow") or None,
            "cta_primary_label": request.form.get("cta_primary_label") or None,
            "cta_primary_href": request.form.get("cta_primary_href") or None,
            "cta_secondary_label": (
                request.form.get("cta_secondary_label") or None
            ),
            "cta_secondary_href": (
                request.form.get("cta_secondary_href") or None
            ),
            "news_panel_eyebrow": (
                request.form.get("news_panel_eyebrow") or None
            ),
            "news_panel_title": request.form.get("news_panel_title") or None,
        }

        db.session.commit()
        flash_ok("Hero principal guardado.")
        return redirect(url_for("admin.home_hero_settings"))

    media_assets = (
        MediaAsset.query
        .filter(MediaAsset.mime_type.like("image/%"))
        .order_by(MediaAsset.created_at.desc())
        .all()
    )
    return render_template(
        "admin/home_hero_form.html",
        site=site,
        hero_block=hero_block,
        hero_config=hero_config,
        media_assets=media_assets,
    )


def _get_or_create_about_block() -> PageBlock:
    block = (
        PageBlock.query
        .filter_by(page_type="home", block_type="tourism_highlights")
        .first()
    )
    if block:
        return block

    block = PageBlock(
        page_type="home",
        block_type="tourism_highlights",
        order_index=3,
        title="",
        subtitle="",
        is_active=True,
        config_json={"eyebrow": "", "items": []},
    )
    db.session.add(block)
    db.session.commit()
    return block


@admin_bp.route("/settings/about", methods=["GET", "POST"])
@login_required
def about_settings():
    import json as _json

    block = _get_or_create_about_block()

    if request.method == "POST":
        block.is_active = request.form.get("is_active") == "on"
        block.title = request.form.get("title") or None
        block.subtitle = request.form.get("subtitle") or None

        eyebrow = (request.form.get("eyebrow") or "").strip() or None

        cards_raw = request.form.get("cards_json", "[]")
        try:
            cards = _json.loads(cards_raw)
            if not isinstance(cards, list):
                cards = []
            import re as _re

            def _hex_color(val: object) -> str | None:
                s = str(val or "").strip()
                return s if _re.fullmatch(r"#[0-9a-fA-F]{6}", s) else None

            cards = [
                {
                    "title": str(c.get("title", "")).strip(),
                    "text": str(c.get("text", "")).strip(),
                    "color_from": _hex_color(c.get("color_from")),
                    "color_to": _hex_color(c.get("color_to")),
                }
                for c in cards
                if (
                    str(c.get("title", "")).strip()
                    or str(c.get("text", "")).strip()
                )
            ]
        except Exception:
            cards = []

        block.config_json = {
            "eyebrow": eyebrow,
            "items": cards,
        }

        db.session.commit()
        flash_ok("Sección 'Nosotros' guardada.")
        return redirect(url_for("admin.about_settings"))

    return render_template("admin/about_form.html", block=block)


def _get_or_create_events_preview_block() -> PageBlock:
    block = (
        PageBlock.query
        .filter_by(page_type="home", block_type="events_preview")
        .first()
    )
    if block:
        return block
    block = PageBlock(
        page_type="home",
        block_type="events_preview",
        order_index=4,
        title="Agenda local",
        subtitle="Actividades comunitarias y servicios",
        is_active=True,
        config_json={},
    )
    db.session.add(block)
    db.session.commit()
    return block


@admin_bp.route("/settings/agenda", methods=["GET", "POST"])
@login_required
def agenda_settings():
    block = _get_or_create_events_preview_block()
    if request.method == "POST":
        block.is_active = request.form.get("is_active") == "on"
        block.title = request.form.get("title") or None
        block.subtitle = request.form.get("subtitle") or None
        block.media_id = _optional_int(request.form.get("media_id"))
        db.session.commit()
        flash_ok("Configuración de Agenda guardada.")
        return redirect(url_for("admin.agenda_settings"))

    media_assets = (
        MediaAsset.query
        .filter(MediaAsset.mime_type.like("image/%"))
        .order_by(MediaAsset.created_at.desc())
        .all()
    )
    return render_template(
        "admin/agenda_settings_form.html",
        block=block,
        media_assets=media_assets,
    )


@admin_bp.route("/settings/theme", methods=["GET", "POST"])
@login_required
def theme_settings():
    t = ThemeSettings.get_settings()
    if request.method == "POST":
        preset = request.form.get("preset", "sierra")
        is_applying_preset = (
            request.form.get("action") == "apply_preset"
            and preset in THEME_PRESET_VALUES
        )
        if is_applying_preset:
            preset_values = THEME_PRESET_VALUES[preset]
            t.preset = preset
            for field, value in preset_values.items():
                setattr(t, field, value)
        else:
            t.preset = preset
            t.primary_color = request.form.get("primary_color", "#2f6f4e")
            t.secondary_color = request.form.get("secondary_color", "#1f3a2c")
            t.accent_color = request.form.get("accent_color", "#d6a84b")
            t.background_color = request.form.get(
                "background_color",
                "#fafaf7",
            )
            t.text_color = request.form.get("text_color", "#1a1a1a")
            t.background_gradient_from = request.form.get(
                "background_gradient_from",
                "#f8fbf7",
            )
            t.background_gradient_to = request.form.get(
                "background_gradient_to",
                "#eef5ef",
            )
            try:
                t.background_gradient_angle = int(
                    request.form.get("background_gradient_angle", 180)
                )
            except (TypeError, ValueError):
                t.background_gradient_angle = 180
        t.header_variant = request.form.get("header_variant", "classic")
        t.footer_variant = request.form.get("footer_variant", "standard")
        t.card_style = request.form.get("card_style", "soft")
        t.hero_style = request.form.get("hero_style", "image-full")
        t.font_style = request.form.get("font_style", "inter")
        t.enable_dark_section = request.form.get("enable_dark_section") == "on"
        t.custom_css = request.form.get("custom_css")
        db.session.commit()
        flash_ok("Tema guardado.")
        return redirect(url_for("admin.theme_settings"))

    return render_template(
        "admin/theme_form.html",
        theme=t,
        presets=THEME_PRESETS,
        header_variants=HEADER_VARIANTS,
        footer_variants=FOOTER_VARIANTS,
        card_styles=CARD_STYLES,
        hero_styles=HERO_STYLES,
        font_styles=FONT_STYLES,
        municipality={"name": "Configuración del Tema"},
    )
