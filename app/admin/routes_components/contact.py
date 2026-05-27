"""Contactos recibidos."""
from flask import redirect, render_template, request, url_for
from flask_login import login_required
from app.admin import admin_bp
from app.admin.routes_components._helpers import flash_err, flash_ok
from app.extensions import db
from app.models.forms import ContactMessage

@admin_bp.route("/contact")
@login_required
def contact_list():
    msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template("admin/contact_list.html", messages=msgs)

@admin_bp.route("/contact/<int:msg_id>")
@login_required
def contact_read(msg_id):
    m = ContactMessage.query.get_or_404(msg_id)
    m.is_read = True
    db.session.commit()
    return render_template("admin/contact_detail.html", msg=m)

@admin_bp.route("/contact/<int:msg_id>/delete", methods=["POST"])
@login_required
def contact_delete(msg_id):
    m = ContactMessage.query.get_or_404(msg_id)
    db.session.delete(m)
    db.session.commit()
    flash_ok("Mensaje eliminado.")
    return redirect(url_for("admin.contact_list"))
