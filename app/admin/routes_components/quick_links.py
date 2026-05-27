"""Administración de Accesos Rápidos (quick_links PageBlock)."""
from flask import abort, redirect, render_template, request, url_for
from flask_login import login_required
from sqlalchemy.orm.attributes import flag_modified

from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_ok
from app.extensions import db
from app.models.settings import PageBlock


def _get_block() -> PageBlock:
    """Devuelve (y crea si no existe) el PageBlock quick_links del home."""
    block = PageBlock.query.filter_by(page_type="home", block_type="quick_links").first()
    if not block:
        block = PageBlock(
            page_type="home",
            block_type="quick_links",
            title="Accesos Rápidos",
            is_active=True,
            config_json={"links": []},
        )
        db.session.add(block)
        db.session.commit()
    if block.config_json is None:
        block.config_json = {"links": []}
        db.session.commit()
    return block


@admin_bp.route("/quick-links")
@login_required
def quick_links_list():
    block = _get_block()
    links = block.config_json.get("links", [])
    return render_template("admin/quick_links.html", block=block, links=links)


@admin_bp.route("/quick-links/add", methods=["POST"])
@login_required
def quick_link_add():
    block = _get_block()
    links = list(block.config_json.get("links", []))
    links.append({
        "label": request.form.get("label", "").strip(),
        "url": request.form.get("url", "").strip(),
        "description": request.form.get("description", "").strip(),
        "icon": request.form.get("icon", "file-text").strip() or "file-text",
    })
    block.config_json = {**block.config_json, "links": links}
    flag_modified(block, "config_json")
    db.session.commit()
    flash_ok("Acceso rápido añadido.")
    return redirect(url_for("admin.quick_links_list"))


@admin_bp.route("/quick-links/<int:index>/edit", methods=["GET", "POST"])
@login_required
def quick_link_edit(index):
    block = _get_block()
    links = list(block.config_json.get("links", []))
    if index < 0 or index >= len(links):
        abort(404)
    if request.method == "POST":
        links[index] = {
            "label": request.form.get("label", "").strip(),
            "url": request.form.get("url", "").strip(),
            "description": request.form.get("description", "").strip(),
            "icon": request.form.get("icon", "file-text").strip() or "file-text",
        }
        block.config_json = {**block.config_json, "links": links}
        flag_modified(block, "config_json")
        db.session.commit()
        flash_ok("Acceso rápido actualizado.")
        return redirect(url_for("admin.quick_links_list"))
    return render_template("admin/quick_link_form.html", link=links[index], index=index)


@admin_bp.route("/quick-links/<int:index>/delete", methods=["POST"])
@login_required
def quick_link_delete(index):
    block = _get_block()
    links = list(block.config_json.get("links", []))
    if index < 0 or index >= len(links):
        abort(404)
    links.pop(index)
    block.config_json = {**block.config_json, "links": links}
    flag_modified(block, "config_json")
    db.session.commit()
    flash_ok("Acceso rápido eliminado.")
    return redirect(url_for("admin.quick_links_list"))


@admin_bp.route("/quick-links/<int:index>/move", methods=["POST"])
@login_required
def quick_link_move(index):
    direction = request.form.get("direction")
    block = _get_block()
    links = list(block.config_json.get("links", []))
    target = index - 1 if direction == "up" else index + 1
    if 0 <= target < len(links):
        links[index], links[target] = links[target], links[index]
        block.config_json = {**block.config_json, "links": links}
        flag_modified(block, "config_json")
        db.session.commit()
    return redirect(url_for("admin.quick_links_list"))
