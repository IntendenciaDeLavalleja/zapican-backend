"""CRUD de eventos."""
from datetime import datetime
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.content import EVENT_STATUSES, Event
from app.models.media import MediaAsset
from app.services.sanitize_service import sanitize_html
from app.utils.slug import ensure_unique_slug, slugify

def _parse_dt(value): return datetime.fromisoformat(value) if value else None
def _maybe_int(v): return int(v) if v else None
def _maybe_float(v): return float(v) if v not in (None, "") else None

@admin_bp.route("/events")
@login_required
def events_list():
    items = Event.query.order_by(Event.start_datetime.desc()).all()
    return render_template("admin/events_list.html", events=items, statuses=EVENT_STATUSES)

@admin_bp.route("/events/new", methods=["GET", "POST"])
@login_required
def event_new():
    if request.method == "POST":
        ev, err = _save(None)
        if err:
            flash_err(err)
        else:
            flash_ok("Evento creado.")
            return redirect(url_for("admin.event_edit", event_id=ev.id))
    return render_template("admin/event_form.html", event=None, statuses=EVENT_STATUSES,
                           media_assets=_image_media_assets())


@admin_bp.route("/events/<int:event_id>/edit", methods=["GET", "POST"])
@login_required
def event_edit(event_id):
    ev = Event.query.get_or_404(event_id)
    if request.method == "POST":
        _, err = _save(ev)
        if err:
            flash_err(err)
        else:
            flash_ok("Evento actualizado.")
            return redirect(url_for("admin.event_edit", event_id=ev.id))
    return render_template("admin/event_form.html", event=ev, statuses=EVENT_STATUSES,
                           media_assets=_image_media_assets())

def _save(ev):
    title = (request.form.get("title") or "").strip()
    if not title: return None, "Titulo requerido."
    start_dt = _parse_dt(request.form.get("start_datetime"))
    if not start_dt: return None, "Fecha de inicio invalida."
    slug = (request.form.get("slug") or "").strip().lower() or slugify(title, 260)
    
    if ev is None:
        slug = ensure_unique_slug(Event, "slug", slug)
        ev = Event(slug=slug)
        db.session.add(ev)
    elif slug != ev.slug:
        slug = ensure_unique_slug(Event, "slug", slug, ignore_id=ev.id)

    ev.title = title
    ev.slug = slug
    ev.description_html = sanitize_html(request.form.get("description_html") or "")
    ev.start_datetime = start_dt
    ev.end_datetime = _parse_dt(request.form.get("end_datetime"))
    ev.location_name = (request.form.get("location_name") or "").strip() or None
    ev.address = (request.form.get("address") or "").strip() or None
    ev.category = (request.form.get("category") or "").strip() or None
    try:
        ev.latitude = _maybe_float(request.form.get("latitude"))
        ev.longitude = _maybe_float(request.form.get("longitude"))
    except (TypeError, ValueError):
        return None, "Coordenadas inválidas."
    status = request.form.get("status", "draft")
    ev.status = status if status in EVENT_STATUSES else "draft"
    ev.is_featured = request.form.get("is_featured") == "on"
    try: 
        ev.cover_media_id = _maybe_int(request.form.get("cover_media_id"))
    except: pass
    db.session.commit()
    return ev, None


def _image_media_assets():
    return (
        MediaAsset.query
        .filter(MediaAsset.mime_type.like("image/%"))
        .order_by(MediaAsset.created_at.desc())
        .all()
    )

@admin_bp.route("/events/<int:event_id>/delete", methods=["POST"])
@login_required
def event_delete(event_id):
    ev = Event.query.get_or_404(event_id)
    db.session.delete(ev)
    db.session.commit()
    flash_ok("Evento eliminado.")
    return redirect(url_for("admin.events_list"))
