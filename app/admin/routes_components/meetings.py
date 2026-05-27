"""CRUD de reuniones."""
from datetime import datetime
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.content import MEETING_STATUSES, MunicipalMeeting
from app.models.media import MediaAsset
@admin_bp.route("/meetings")
@login_required
def meetings_list():
    items = MunicipalMeeting.query.order_by(MunicipalMeeting.meeting_datetime.desc()).all()
    return render_template("admin/meetings_list.html", meetings=items, statuses=MEETING_STATUSES)

@admin_bp.route("/meetings/new", methods=["GET", "POST"])
@login_required
def meeting_new():
    if request.method == "POST":
        m = MunicipalMeeting()
        m = _save(m)
        db.session.add(m)
        db.session.commit()
        flash_ok("Reunión creada.")
        return redirect(url_for("admin.meetings_list"))
    return render_template("admin/meeting_form.html", meeting=None, statuses=MEETING_STATUSES,
                           media_assets=_all_media_assets())

@admin_bp.route("/meetings/<int:meeting_id>/edit", methods=["GET", "POST"])
@login_required
def meeting_edit(meeting_id):
    m = MunicipalMeeting.query.get_or_404(meeting_id)
    if request.method == "POST":
        _save(m)
        db.session.commit()
        flash_ok("Reunión actualizada.")
        return redirect(url_for("admin.meeting_edit", meeting_id=m.id))
    return render_template("admin/meeting_form.html", meeting=m, statuses=MEETING_STATUSES,
                           media_assets=_all_media_assets())

def _save(m):
    m.title = request.form.get("title")
    dt = request.form.get("meeting_datetime")
    if dt: m.meeting_datetime = datetime.fromisoformat(dt)
    m.description = request.form.get("description")
    m.location_name = request.form.get("location_name")
    m.address = request.form.get("address")
    m.agenda_html = request.form.get("agenda_html")
    m.minutes_html = request.form.get("minutes_html")
    m.status = request.form.get("status", "scheduled")
    m.is_public = request.form.get("is_public") == "on"
    try: m.document_media_id = int(request.form.get("document_media_id")) if request.form.get("document_media_id") else None
    except: pass
    return m

def _all_media_assets():
    return (
        MediaAsset.query
        .order_by(MediaAsset.created_at.desc())
        .all()
    )

@admin_bp.route("/meetings/<int:meeting_id>/delete", methods=["POST"])
@login_required
def meeting_delete(meeting_id):
    m = MunicipalMeeting.query.get_or_404(meeting_id)
    db.session.delete(m)
    db.session.commit()
    flash_ok("Reunión eliminada.")
    return redirect(url_for("admin.meetings_list"))
