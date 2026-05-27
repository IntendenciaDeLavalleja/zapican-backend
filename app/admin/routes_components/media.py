"""Carga y gestión de medios."""
from flask import jsonify, redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.models.media import MediaAsset
from app.services.minio_service import minio_service
from app.extensions import db


@admin_bp.route("/media", methods=["GET"])
@login_required
def media_library():
    page = request.args.get("page", 1, type=int)
    pagination = MediaAsset.query.order_by(
        MediaAsset.created_at.desc()
    ).paginate(page=page, per_page=30)
    return render_template(
        "admin/media_list.html",
        assets=pagination.items,
        pagination=pagination,
    )


@admin_bp.route("/media/upload", methods=["POST"])
@login_required
def media_upload():
    f = request.files.get("file")
    if not f or not f.filename:
        return jsonify({"error": "No hay archivo"}), 400
    if f.mimetype != "image/webp":
        return jsonify({"error": "Solo se permiten imágenes WebP."}), 400
    try:
        data = minio_service.upload_stream(
            f,
            f.mimetype or "application/octet-stream",
            original_name=f.filename,
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    original_filename = (
        (request.form.get("original_filename") or "").strip()
        or f.filename
    )

    asset = MediaAsset(
        filename=data["object_name"],
        original_filename=original_filename,
        mime_type=f.mimetype or "application/octet-stream",
        size_bytes=data["size"],
        public_url=data["public_url"],
        is_public=True
    )
    db.session.add(asset)
    db.session.commit()
    flash_ok("Archivo subido.")
    return redirect(url_for("admin.media_library"))


@admin_bp.route("/media/<int:asset_id>/edit", methods=["POST"])
@login_required
def media_update(asset_id):
    asset = MediaAsset.query.get_or_404(asset_id)
    uploaded_file = request.files.get("file")
    requested_name = (request.form.get("original_filename") or "").strip()

    asset.original_filename = requested_name or asset.original_filename
    asset.is_public = request.form.get("is_public") == "on"

    if uploaded_file and uploaded_file.filename:
        if uploaded_file.mimetype != "image/webp":
            flash_err("Solo se permiten imágenes WebP.")
            return redirect(url_for("admin.media_library"))
        old_object_name = asset.filename
        try:
            data = minio_service.upload_stream(
                uploaded_file,
                uploaded_file.mimetype or "application/octet-stream",
                original_name=uploaded_file.filename,
            )
            asset.filename = data["object_name"]
            asset.mime_type = (
                uploaded_file.mimetype or "application/octet-stream"
            )
            asset.size_bytes = data["size"]
            asset.public_url = data["public_url"]
            if not requested_name:
                asset.original_filename = uploaded_file.filename
            db.session.commit()
        except Exception as exc:
            db.session.rollback()
            flash_err(f"No se pudo actualizar el medio: {exc}")
            return redirect(url_for("admin.media_library"))

        if old_object_name != asset.filename:
            minio_service.remove(old_object_name)
    else:
        db.session.commit()

    flash_ok("Medio actualizado.")
    return redirect(url_for("admin.media_library"))


@admin_bp.route("/media/<int:asset_id>/delete", methods=["POST"])
@login_required
def media_delete(asset_id):
    asset = MediaAsset.query.get_or_404(asset_id)
    try:
        minio_service.remove(asset.filename)
    except Exception:
        pass
    db.session.delete(asset)
    db.session.commit()
    flash_ok("Archivo eliminado.")
    return redirect(url_for("admin.media_library"))
