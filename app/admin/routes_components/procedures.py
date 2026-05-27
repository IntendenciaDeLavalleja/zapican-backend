"""CRUD de trámites y solicitudes de trámites."""
from __future__ import annotations

from flask import redirect, render_template, request, url_for
from flask_login import login_required

from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_ok
from app.extensions import db
from app.models import PROCEDURE_SUBMISSION_STATUSES, ProcedureSubmission, ProcedureType
from app.utils.slug import ensure_unique_slug, slugify


def _parse_required_documents(raw: str | None) -> list[str]:
    return [line.strip() for line in (raw or "").splitlines() if line.strip()]


@admin_bp.route("/procedures")
@login_required
def procedures_list():
    items = ProcedureType.query.order_by(ProcedureType.order_index.asc(), ProcedureType.title.asc()).all()
    new_count = ProcedureSubmission.query.filter_by(status="new").count()
    return render_template("admin/procedures_list.html", procedures=items, new_count=new_count)


@admin_bp.route("/procedures/new", methods=["GET", "POST"])
@login_required
def procedure_new():
    if request.method == "POST":
        item = ProcedureType()
        item.title = (request.form.get("title") or "").strip()
        slug = (request.form.get("slug") or slugify(item.title)).strip()
        item.slug = ensure_unique_slug(ProcedureType, "slug", slug)
        item.summary = (request.form.get("summary") or "").strip() or None
        item.description_html = (request.form.get("description_html") or "").strip() or None
        item.eligibility_notes = (request.form.get("eligibility_notes") or "").strip() or None
        item.fee_text = (request.form.get("fee_text") or "").strip() or None
        item.required_documents_json = _parse_required_documents(request.form.get("required_documents"))
        item.is_active = request.form.get("is_active") == "on"
        item.is_featured = request.form.get("is_featured") == "on"
        try:
            item.order_index = int(request.form.get("order_index") or 0)
        except ValueError:
            item.order_index = 0
        try:
            item.estimated_days = int(request.form.get("estimated_days") or 0) or None
        except ValueError:
            item.estimated_days = None
        db.session.add(item)
        db.session.commit()
        flash_ok("Trámite creado.")
        return redirect(url_for("admin.procedure_edit", procedure_id=item.id))
    return render_template("admin/procedure_form.html", procedure=None)


@admin_bp.route("/procedures/<int:procedure_id>/edit", methods=["GET", "POST"])
@login_required
def procedure_edit(procedure_id):
    item = ProcedureType.query.get_or_404(procedure_id)
    if request.method == "POST":
        item.title = (request.form.get("title") or "").strip()
        slug = (request.form.get("slug") or slugify(item.title)).strip()
        if slug != item.slug:
            item.slug = ensure_unique_slug(ProcedureType, "slug", slug, ignore_id=item.id)
        item.summary = (request.form.get("summary") or "").strip() or None
        item.description_html = (request.form.get("description_html") or "").strip() or None
        item.eligibility_notes = (request.form.get("eligibility_notes") or "").strip() or None
        item.fee_text = (request.form.get("fee_text") or "").strip() or None
        item.required_documents_json = _parse_required_documents(request.form.get("required_documents"))
        item.is_active = request.form.get("is_active") == "on"
        item.is_featured = request.form.get("is_featured") == "on"
        try:
            item.order_index = int(request.form.get("order_index") or 0)
        except ValueError:
            pass
        try:
            item.estimated_days = int(request.form.get("estimated_days") or 0) or None
        except ValueError:
            item.estimated_days = None
        db.session.commit()
        flash_ok("Trámite actualizado.")
        return redirect(url_for("admin.procedure_edit", procedure_id=item.id))
    return render_template("admin/procedure_form.html", procedure=item)


@admin_bp.route("/procedures/<int:procedure_id>/delete", methods=["POST"])
@login_required
def procedure_delete(procedure_id):
    item = ProcedureType.query.get_or_404(procedure_id)
    db.session.delete(item)
    db.session.commit()
    flash_ok("Trámite eliminado.")
    return redirect(url_for("admin.procedures_list"))


@admin_bp.route("/procedures/submissions")
@login_required
def procedure_submissions():
    selected_status = (request.args.get("status") or "").strip()
    selected_type = request.args.get("procedure_id", type=int)

    query = ProcedureSubmission.query.order_by(ProcedureSubmission.created_at.desc())
    if selected_status in PROCEDURE_SUBMISSION_STATUSES:
        query = query.filter(ProcedureSubmission.status == selected_status)
    if selected_type:
        query = query.filter(ProcedureSubmission.procedure_type_id == selected_type)

    submissions = query.all()
    procedure_types = ProcedureType.query.order_by(ProcedureType.title.asc()).all()
    return render_template(
        "admin/procedure_submissions.html",
        submissions=submissions,
        procedure_types=procedure_types,
        statuses=PROCEDURE_SUBMISSION_STATUSES,
        selected_status=selected_status,
        selected_type=selected_type,
    )


@admin_bp.route("/procedures/submissions/<int:submission_id>")
@login_required
def procedure_submission_detail(submission_id):
    submission = ProcedureSubmission.query.get_or_404(submission_id)
    return render_template(
        "admin/procedure_submission_detail.html",
        submission=submission,
        statuses=PROCEDURE_SUBMISSION_STATUSES,
    )


@admin_bp.route("/procedures/submissions/<int:submission_id>/update", methods=["POST"])
@login_required
def procedure_submission_update(submission_id):
    submission = ProcedureSubmission.query.get_or_404(submission_id)
    status = (request.form.get("status") or "").strip()
    submission.status = status if status in PROCEDURE_SUBMISSION_STATUSES else "new"
    submission.internal_notes = (request.form.get("internal_notes") or "").strip() or None
    db.session.commit()
    flash_ok("Solicitud actualizada.")
    return redirect(url_for("admin.procedure_submissions"))