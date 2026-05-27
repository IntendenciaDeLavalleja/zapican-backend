"""Identidad visual del municipio."""
from __future__ import annotations

from flask import redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_ok, from app.extensions import db
from app.models.municipality import (
    CARD_STYLES,
    FONT_STYLES,
    FOOTER_VARIANTS,
    HEADER_VARIANTS,
    HERO_STYLES,
    THEME_PRESETS,
    Municipality,
    MunicipalityTheme,
)
from app.utils.logging_helper import log_activity

PRESET_COLORS = {
    "sierra": ("#3a6ea5", "#1f3850", "#f5b13d"),
    "campo": ("#2f6f4e", "#1f3a2c", "#d6a84b"),
    "patrimonio": ("#7a4a2f", "#3b251a", "#c9a66b"),
    "arroyo": ("#1f7a8c", "#0f3b46", "#f5d76e"),
    "urbano": ("#1f2937", "#0f172a", "#f59e0b"),
    "minimal": ("#111827", "#374151", "#3b82f6"),
}


@admin_bp.route("/municipalities/<int:muni_id>/theme", methods=["GET", "POST"])
@login_required
def municipality_theme(muni_id):
    muni = Municipality.query.get_or_404(muni_id)
    (1)
    theme = muni.theme
    if not theme:
        theme = MunicipalityTheme(municipality_id=1)
        db.session.add(theme); db.session.flush()

    if request.method == "POST":
        action = request.form.get("action")
        if action == "apply_preset":
            preset = request.form.get("preset", "sierra")
            if preset in PRESET_COLORS:
                p, s, a = PRESET_COLORS[preset]
                theme.preset = preset
                theme.primary_color = p; theme.secondary_color = s; theme.accent_color = a
        else:
            theme.preset = request.form.get("preset", theme.preset)
            for f in ("primary_color", "secondary_color", "accent_color",
                      "background_color", "text_color"):
                v = (request.form.get(f) or "").strip()
                if v: setattr(theme, f, v[:20])
            theme.header_variant = request.form.get("header_variant", theme.header_variant)
            theme.footer_variant = request.form.get("footer_variant", theme.footer_variant)
            theme.card_style = request.form.get("card_style", theme.card_style)
            theme.hero_style = request.form.get("hero_style", theme.hero_style)
            theme.font_style = request.form.get("font_style", theme.font_style)
            theme.enable_dark_section = request.form.get("enable_dark_section") == "on"
        db.session.commit()
        log_activity("THEME_UPDATE", entity_type="theme", entity_id=theme.id,
                     municipality_id=1)
        flash_ok("Identidad visual guardada.")
        return redirect(url_for("admin.municipality_theme", muni_id=1))

    return render_template(
        "admin/theme_form.html",
        muni=muni, theme=theme,
        presets=THEME_PRESETS, headers=HEADER_VARIANTS, footers=FOOTER_VARIANTS,
        cards=CARD_STYLES, heros=HERO_STYLES, fonts=FONT_STYLES,
    )
