"""Configuración de colores del encabezado de la página de Novedades."""
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm.attributes import flag_modified

from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_ok
from app.extensions import db
from app.models.settings import PageBlock, ThemeSettings

_DEFAULTS = {
    "heading_color": "#0f172a",
    "subtitle_color": "#475569",
    "label_color": "#64748b",
}


def _get_block() -> PageBlock:
    block = PageBlock.query.filter_by(
        page_type="novedades", block_type="news_header"
    ).first()
    if not block:
        block = PageBlock(
            page_type="novedades",
            block_type="news_header",
            title="Encabezado Novedades",
            is_active=True,
            config_json=dict(_DEFAULTS),
        )
        db.session.add(block)
        db.session.commit()
    if block.config_json is None:
        block.config_json = dict(_DEFAULTS)
        db.session.commit()
    return block


@admin_bp.route("/novedades-settings", methods=["GET", "POST"])
@login_required
def novedades_settings():
    block = _get_block()
    theme = ThemeSettings.get_settings()
    if request.method == "POST":
        block.config_json = {
            "heading_color": request.form.get("heading_color") or _DEFAULTS["heading_color"],
            "subtitle_color": request.form.get("subtitle_color") or _DEFAULTS["subtitle_color"],
            "label_color": request.form.get("label_color") or _DEFAULTS["label_color"],
        }
        flag_modified(block, "config_json")
        db.session.commit()
        flash_ok("Colores guardados.")
        return redirect(url_for("admin.novedades_settings"))
    cfg = {**_DEFAULTS, **(block.config_json or {})}
    return render_template(
        "admin/novedades_settings.html",
        cfg=cfg,
        bg_from=theme.background_gradient_from,
        bg_to=theme.background_gradient_to,
        bg_angle=theme.background_gradient_angle,
    )
