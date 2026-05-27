"""CRUD de calendario."""
from datetime import datetime
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.content import CalendarItem, CALENDAR_TYPES


def _parse_dt(raw_value):
    value = (raw_value or "").strip()
    if not value:
        return None
    return datetime.fromisoformat(value)


def _save_calendar_item(item: CalendarItem | None):
    title = (request.form.get("title") or "").strip()
    if not title:
        return None, "Título requerido."

    start_datetime = _parse_dt(request.form.get("start_datetime"))
    if not start_datetime:
        return None, "Fecha de inicio inválida."

    if item is None:
        item = CalendarItem()
        db.session.add(item)

    item.title = title
    item.description = (request.form.get("description") or "").strip() or None
    item.type = request.form.get("type", "notice")
    if item.type not in CALENDAR_TYPES:
        item.type = "notice"
    item.location = (request.form.get("location") or "").strip() or None
    item.status = (request.form.get("status") or "published").strip() or "published"
    item.start_datetime = start_datetime
    item.end_datetime = _parse_dt(request.form.get("end_datetime"))
    db.session.commit()
    return item, None


@admin_bp.route("/calendar")
@login_required
def calendar_list():
    items = CalendarItem.query.order_by(CalendarItem.start_datetime.desc()).all()
    return render_template("admin/calendar.html", items=items, item_types=CALENDAR_TYPES)

@admin_bp.route("/calendar/new", methods=["GET", "POST"])
@login_required
def calendar_create():
    if request.method == "POST":
        item, err = _save_calendar_item(None)
        if err:
            flash_err(err)
        else:
            flash_ok("Item agregado.")
            return redirect(url_for("admin.calendar_edit", item_id=item.id))
    return render_template("admin/calendar_form.html", item=None, item_types=CALENDAR_TYPES)


@admin_bp.route("/calendar/<int:item_id>/edit", methods=["GET", "POST"])
@login_required
def calendar_edit(item_id):
    item = CalendarItem.query.get_or_404(item_id)
    if request.method == "POST":
        _, err = _save_calendar_item(item)
        if err:
            flash_err(err)
        else:
            flash_ok("Item actualizado.")
            return redirect(url_for("admin.calendar_edit", item_id=item.id))
    return render_template("admin/calendar_form.html", item=item, item_types=CALENDAR_TYPES)

@admin_bp.route("/calendar/<int:item_id>/delete", methods=["POST"])
@login_required
def calendar_delete(item_id):
    i = CalendarItem.query.get_or_404(item_id)
    db.session.delete(i)
    db.session.commit()
    flash_ok("Item de calendario eliminado.")
    return redirect(url_for("admin.calendar_list"))
