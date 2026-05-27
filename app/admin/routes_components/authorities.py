"""CRUD de Autoridades."""
from flask import redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_ok
from app.extensions import db
from app.models.media import MediaAsset
from app.models.settings import Authority


@admin_bp.route("/authorities")
@login_required
def authorities_list():
    items = Authority.query.order_by(Authority.order_index).all()
    return render_template("admin/authorities_list.html", authorities=items)


@admin_bp.route("/authorities/new", methods=["GET", "POST"])
@login_required
def authority_new():
    if request.method == "POST":
        a = Authority()
        _save(a)
        db.session.add(a)
        db.session.commit()
        flash_ok("Autoridad creada.")
        return redirect(url_for("admin.authorities_list"))
    return render_template(
        "admin/authority_form.html",
        authority=None,
        media_assets=_image_media_assets(),
    )


@admin_bp.route("/authorities/<int:auth_id>/edit", methods=["GET", "POST"])
@login_required
def authority_edit(auth_id):
    a = Authority.query.get_or_404(auth_id)
    if request.method == "POST":
        _save(a)
        db.session.commit()
        flash_ok("Autoridad actualizada.")
        return redirect(url_for("admin.authority_edit", auth_id=a.id))
    return render_template(
        "admin/authority_form.html",
        authority=a,
        media_assets=_image_media_assets(),
    )


def _image_media_assets():
    return (
        MediaAsset.query
        .filter(MediaAsset.mime_type.like("image/%"))
        .order_by(MediaAsset.created_at.desc())
        .all()
    )


def _save(a):
    a.name = request.form.get("name")
    a.role = request.form.get("role")
    a.bio = request.form.get("bio")
    a.email = request.form.get("email")
    a.phone = request.form.get("phone")
    a.facebook_url = request.form.get("facebook_url")
    a.twitter_url = request.form.get("twitter_url")
    a.linkedin_url = request.form.get("linkedin_url")
    try:
        a.order_index = int(request.form.get("order_index") or 0)
    except Exception:
        pass
    try:
        val = request.form.get("photo_media_id")
        a.photo_media_id = int(val) if val else None
    except Exception:
        pass


@admin_bp.route("/authorities/<int:auth_id>/delete", methods=["POST"])
@login_required
def authority_delete(auth_id):
    a = Authority.query.get_or_404(auth_id)
    db.session.delete(a)
    db.session.commit()
    flash_ok("Autoridad eliminada.")
    return redirect(url_for("admin.authorities_list"))
