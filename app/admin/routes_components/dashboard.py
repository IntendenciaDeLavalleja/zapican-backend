"""Dashboard principal."""
from datetime import datetime
from flask import render_template
from flask_login import login_required
from app.admin import admin_bp
from app.extensions import db
from app.models.content import NewsPost, Event, MunicipalMeeting
from app.models.forms import FormSubmission, ContactMessage
from app.models.user import AuditLog

@admin_bp.route("/")
@login_required
def dashboard():
    now = datetime.utcnow()
    stats = {
        "news_published": db.session.query(NewsPost).filter_by(status="published").count(),
        "news_draft": db.session.query(NewsPost).filter_by(status="draft").count(),
        "upcoming_events": db.session.query(Event).filter(Event.start_datetime >= now).count(),
        "upcoming_meetings": db.session.query(MunicipalMeeting).filter(MunicipalMeeting.meeting_datetime >= now).count(),
        "new_messages": db.session.query(ContactMessage).filter_by(is_read=False).count(),
        "new_submissions": db.session.query(FormSubmission).count(),
    }
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(10).all()
    return render_template("admin/dashboard.html", stats=stats, recent_logs=logs)
