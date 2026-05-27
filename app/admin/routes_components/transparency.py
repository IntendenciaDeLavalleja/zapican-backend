"""Solicitudes de acceso a la información pública — panel administrativo."""
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.transparency import TransparencyRequest


STATUS_LABELS = {
    "new": "Nueva",
    "in_review": "En revisión",
    "answered": "Respondida",
    "archived": "Archivada",
}


@admin_bp.route("/transparency")
@login_required
def transparency_list():
    requests_qs = TransparencyRequest.query.order_by(
        TransparencyRequest.is_read.asc(),
        TransparencyRequest.created_at.desc(),
    ).all()
    return render_template(
        "admin/transparency_list.html",
        requests=requests_qs,
        status_labels=STATUS_LABELS,
    )


@admin_bp.route("/transparency/<int:req_id>")
@login_required
def transparency_detail(req_id: int):
    tr = TransparencyRequest.query.get_or_404(req_id)
    if not tr.is_read:
        tr.is_read = True
        db.session.commit()
    return render_template(
        "admin/transparency_detail.html",
        tr=tr,
        status_labels=STATUS_LABELS,
    )


@admin_bp.route("/transparency/<int:req_id>/status", methods=["POST"])
@login_required
def transparency_set_status(req_id: int):
    tr = TransparencyRequest.query.get_or_404(req_id)
    new_status = request.form.get("status", "").strip()
    from app.models.transparency import TRANSPARENCY_REQUEST_STATUSES
    if new_status not in TRANSPARENCY_REQUEST_STATUSES:
        flash_err("Estado inválido.")
        return redirect(url_for("admin.transparency_detail", req_id=req_id))
    tr.status = new_status
    tr.internal_notes = request.form.get("internal_notes", tr.internal_notes or "").strip() or tr.internal_notes
    db.session.commit()
    flash_ok(f"Estado actualizado a «{STATUS_LABELS.get(new_status, new_status)}».")
    return redirect(url_for("admin.transparency_detail", req_id=req_id))


@admin_bp.route("/transparency/<int:req_id>/delete", methods=["POST"])
@login_required
def transparency_delete(req_id: int):
    tr = TransparencyRequest.query.get_or_404(req_id)
    db.session.delete(tr)
    db.session.commit()
    flash_ok("Solicitud eliminada.")
    return redirect(url_for("admin.transparency_list"))
