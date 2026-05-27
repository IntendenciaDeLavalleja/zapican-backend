"""CRUD de Bloques de Portada."""
import json
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.settings import BLOCK_TYPES, PAGE_TYPES, PageBlock

@admin_bp.route("/pages/<page_type>/blocks")
@login_required
def blocks_list(page_type):
    if page_type not in PAGE_TYPES: page_type = "home"
    items = PageBlock.query.filter_by(page_type=page_type).order_by(PageBlock.order_index.asc()).all()
    return render_template("admin/blocks_list.html", blocks=items, page_type=page_type, ALL_BLOCK_TYPES=BLOCK_TYPES)

@admin_bp.route("/blocks", methods=["POST"])
@login_required
def block_create():
    ptype = request.form.get("page_type")
    btype = request.form.get("block_type")
    title = request.form.get("title")
    if ptype in PAGE_TYPES and btype in BLOCK_TYPES:
        b = PageBlock(page_type=ptype, block_type=btype, title=title, is_active=True)
        db.session.add(b)
        db.session.commit()
        flash_ok("Bloque añadido.")
    return redirect(url_for("admin.blocks_list", page_type=ptype))

@admin_bp.route("/blocks/<int:block_id>/edit", methods=["GET", "POST"])
@login_required
def block_edit(block_id):
    b = PageBlock.query.get_or_404(block_id)
    if request.method == "POST":
        b.title = request.form.get("title")
        b.subtitle = request.form.get("subtitle")
        b.content_html = request.form.get("content_html")
        b.is_active = request.form.get("is_active") == "on"
        try:
            b.order_index = int(request.form.get("order_index") or 0)
        except ValueError:
            pass
        if request.form.get("config_json"):
            try: b.config_json = json.loads(request.form.get("config_json"))
            except: pass
        if request.form.get("media_id"):
            try: b.media_id = int(request.form.get("media_id"))
            except: pass
        db.session.commit()
        flash_ok("Bloque guardado.")
        return redirect(url_for("admin.block_edit", block_id=b.id))
    return render_template("admin/block_form.html", block=b)

@admin_bp.route("/blocks/<int:block_id>/delete", methods=["POST"])
@login_required
def block_delete(block_id):
    b = PageBlock.query.get_or_404(block_id)
    ptype = b.page_type
    db.session.delete(b)
    db.session.commit()
    flash_ok("Bloque eliminado.")
    return redirect(url_for("admin.blocks_list", page_type=ptype))
