"""Formularios dinamicos."""
import json
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.forms import CustomForm, FormField, FormSubmission, FIELD_TYPES, FORM_SUBMISSION_STATUSES
from app.utils.slug import ensure_unique_slug, slugify

@admin_bp.route("/forms")
@login_required
def forms_list():
    forms = CustomForm.query.all()
    return render_template("admin/forms_list.html", forms=forms)

@admin_bp.route("/forms/new", methods=["GET", "POST"])
@login_required
def form_new():
    if request.method == "POST":
        f = CustomForm()
        f.title = (request.form.get("title") or "").strip()
        slug = request.form.get("slug") or slugify(f.title)
        f.slug = ensure_unique_slug(CustomForm, "slug", slug)
        f.description = (request.form.get("description") or "").strip() or None
        f.notify_emails = (request.form.get("notify_emails") or "").strip() or None
        f.is_active = request.form.get("is_active") == "on"
        db.session.add(f)
        db.session.commit()
        flash_ok("Formulario creado.")
        return redirect(url_for("admin.form_edit", form_id=f.id))
    return render_template("admin/form_form.html", form=None, field_types=FIELD_TYPES, editing_field=None)

@admin_bp.route("/forms/<int:form_id>/edit", methods=["GET", "POST"])
@login_required
def form_edit(form_id):
    f = CustomForm.query.get_or_404(form_id)
    if request.method == "POST":
        f.title = (request.form.get("title") or "").strip()
        slug = request.form.get("slug") or slugify(f.title)
        if slug != f.slug:
            f.slug = ensure_unique_slug(CustomForm, "slug", slug, ignore_id=f.id)
        f.description = (request.form.get("description") or "").strip() or None
        f.notify_emails = (request.form.get("notify_emails") or "").strip() or None
        f.is_active = request.form.get("is_active") == "on"
        db.session.commit()
        flash_ok("Formulario actualizado.")
        return redirect(url_for("admin.form_edit", form_id=f.id))
    editing_field = None
    field_id = request.args.get("field_id", type=int)
    if field_id:
        editing_field = FormField.query.filter_by(id=field_id, form_id=f.id).first_or_404()
    return render_template("admin/form_form.html", form=f, field_types=FIELD_TYPES, editing_field=editing_field)

@admin_bp.route("/forms/<int:form_id>/delete", methods=["POST"])
@login_required
def form_delete(form_id):
    f = CustomForm.query.get_or_404(form_id)
    db.session.delete(f)
    db.session.commit()
    flash_ok("Formulario eliminado.")
    return redirect(url_for("admin.forms_list"))

@admin_bp.route("/forms/<int:form_id>/fields", methods=["POST"])
@login_required
def field_create(form_id):
    field = FormField(form_id=form_id)
    field.name = (request.form.get("name") or "").strip()
    field.label = (request.form.get("label") or "").strip()
    field.field_type = request.form.get("field_type")
    if field.field_type not in FIELD_TYPES:
        field.field_type = "text"
    field.is_required = request.form.get("is_required") == "on"
    field.options = (request.form.get("options") or "").strip() or None
    try: field.order_index = int(request.form.get("order_index") or 0)
    except: pass
    db.session.add(field)
    db.session.commit()
    flash_ok("Campo añadido.")
    return redirect(url_for("admin.form_edit", form_id=form_id))


@admin_bp.route("/forms/fields/<int:field_id>/edit", methods=["GET", "POST"])
@login_required
def field_edit(field_id):
    field = FormField.query.get_or_404(field_id)
    if request.method == "POST":
        field.name = (request.form.get("name") or "").strip()
        field.label = (request.form.get("label") or "").strip()
        field.field_type = request.form.get("field_type")
        if field.field_type not in FIELD_TYPES:
            field.field_type = "text"
        field.is_required = request.form.get("is_required") == "on"
        field.options = (request.form.get("options") or "").strip() or None
        try:
            field.order_index = int(request.form.get("order_index") or 0)
        except Exception:
            pass
        db.session.commit()
        flash_ok("Campo actualizado.")
        return redirect(url_for("admin.form_edit", form_id=field.form_id))
    return redirect(url_for("admin.form_edit", form_id=field.form_id, field_id=field.id))

@admin_bp.route("/forms/fields/<int:field_id>/delete", methods=["POST"])
@login_required
def field_delete(field_id):
    field = FormField.query.get_or_404(field_id)
    f_id = field.form_id
    db.session.delete(field)
    db.session.commit()
    flash_ok("Campo eliminado.")
    return redirect(url_for("admin.form_edit", form_id=f_id))

@admin_bp.route("/forms/<int:form_id>/submissions")
@login_required
def form_submissions(form_id):
    f = CustomForm.query.get_or_404(form_id)
    subs = FormSubmission.query.filter_by(form_id=form_id).order_by(FormSubmission.created_at.desc()).all()
    # decodificar json si es str, sino dejar igual
    for s in subs:
        if isinstance(s.data_json, str):
            try: s.data_json = json.loads(s.data_json)
            except: s.data_json = {}
    return render_template("admin/submissions_list.html", form=f, submissions=subs, statuses=FORM_SUBMISSION_STATUSES)

@admin_bp.route("/forms/submissions/<int:sub_id>/update", methods=["POST"])
@login_required
def submission_update(sub_id):
    sub = FormSubmission.query.get_or_404(sub_id)
    status = request.form.get("status")
    sub.status = status if status in FORM_SUBMISSION_STATUSES else "new"
    sub.internal_notes = (request.form.get("internal_notes") or "").strip() or None
    db.session.commit()
    flash_ok("Respuesta actualizada.")
    return redirect(url_for("admin.form_submissions", form_id=sub.form_id))
