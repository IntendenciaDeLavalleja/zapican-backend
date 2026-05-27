"""Endpoints públicos genéricos."""
import json
import uuid
from datetime import datetime

from flask import Blueprint, jsonify, request
from sqlalchemy import or_
from app.models import (
    SiteSettings, ThemeSettings, Authority, PageBlock,
    NewsCategory, NewsPost, Event, MunicipalMeeting, CustomForm, FormSubmission,
    ProcedureType, ProcedureSubmission, CalendarItem,
)
from app.models.media import MediaAsset
from app.models.procedures import procedure_document_field_name
from app.models.transparency import TransparencyRequest
from app.extensions import db
from app.services.minio_service import minio_service
from app.services.email_service import send_email, send_procedure_received
from . import api_bp

@api_bp.route("/site")
def get_site_config():
    site = SiteSettings.get_settings()
    theme = ThemeSettings.get_settings()
    return jsonify({
        "site": site.to_public_dict(),
        "theme": theme.to_public_dict()
    })

@api_bp.route("/authorities")
def list_authorities():
    auths = Authority.query.order_by(Authority.order_index).all()
    return jsonify({"authorities": [a.to_public_dict() for a in auths]})

@api_bp.route("/pages/<page_type>")
def get_page_blocks(page_type):
    blocks = PageBlock.query.filter_by(page_type=page_type, is_active=True).order_by(PageBlock.order_index).all()
    return jsonify({"blocks": [b.to_public_dict() for b in blocks]})

@api_bp.route("/news")
def list_news():
    try:
        page = max(1, int(request.args.get("page") or 1))
        per_page = min(100, max(1, int(request.args.get("per_page") or 50)))
    except (ValueError, TypeError):
        page, per_page = 1, 50
    q = NewsPost.query.filter_by(status="published").order_by(NewsPost.published_at.desc())
    total = q.count()
    posts = q.limit(per_page).offset((page - 1) * per_page).all()
    pages = max(1, (total + per_page - 1) // per_page)
    return jsonify({
        "news": [p.to_summary_dict() for p in posts],
        "page": page,
        "per_page": per_page,
        "total": total,
        "pages": pages,
    })

@api_bp.route("/news/<slug>")
def get_news(slug):
    p = NewsPost.query.filter_by(slug=slug, status="published").first_or_404()
    return jsonify(p.to_public_dict())

@api_bp.route("/events")
def list_events():
    events = Event.query.filter_by(status="published").order_by(Event.start_datetime).all()
    return jsonify({"events": [e.to_summary_dict() for e in events]})

@api_bp.route("/events/<slug>")
def get_event(slug):
    e = Event.query.filter_by(slug=slug, status="published").first_or_404()
    return jsonify(e.to_public_dict())

@api_bp.route("/agenda")
def list_agenda():
    items = (
        CalendarItem.query
        .filter_by(status="published")
        .order_by(CalendarItem.start_datetime)
        .all()
    )
    return jsonify({"agenda": [it.to_public_dict() for it in items]})

@api_bp.route("/meetings")
def list_meetings():
    meetings = MunicipalMeeting.query.filter_by(is_public=True).order_by(MunicipalMeeting.meeting_datetime.desc()).all()
    return jsonify({"meetings": [m.to_public_dict() for m in meetings]})

@api_bp.route("/forms/<slug>")
def get_form(slug):
    f = CustomForm.query.filter_by(slug=slug, is_active=True).first_or_404()
    return jsonify(f.to_public_dict())

@api_bp.route("/forms/<slug>/submit", methods=["POST"])
def submit_form(slug):
    f = CustomForm.query.filter_by(slug=slug, is_active=True).first_or_404()
    data = request.json or {}

    is_contact = "contact" in f.slug.lower() or "contacto" in f.slug.lower()

    from app.models.settings import SiteSettings
    from app.services import email_service as _mail
    site = SiteSettings.get_settings()
    municipality_name = (site.name or "el municipio").strip()

    if is_contact:
        # Guardar como ContactMessage
        from app.models.forms import ContactMessage
        msg = ContactMessage(
            name=(data.get("name") or data.get("nombre") or "").strip(),
            email=(data.get("email") or "").strip(),
            phone=(data.get("phone") or data.get("telefono") or "").strip() or None,
            subject=(data.get("subject") or data.get("asunto") or "").strip() or None,
            message=(data.get("message") or data.get("mensaje") or "").strip(),
            ip_address=request.remote_addr,
        )
        db.session.add(msg)
        db.session.commit()

        # Notificar al/los admin(s)
        if f.notify_emails:
            for addr in [e.strip() for e in f.notify_emails.split(",") if e.strip()]:
                _mail.send_contact_received(
                    addr,
                    municipality_name=municipality_name,
                    subject=msg.subject or "sin asunto",
                    sender_name=msg.name,
                    sender_email=msg.email,
                    message=msg.message,
                )

        # Confirmar al remitente
        if msg.email:
            _mail.send_contact_confirmation(
                msg.email,
                name=msg.name,
                municipality_name=municipality_name,
                subject=msg.subject or "Tu mensaje",
            )
    else:
        sub = FormSubmission(
            form_id=f.id,
            data_json=data,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        db.session.add(sub)
        db.session.commit()

        if f.notify_emails:
            for addr in [e.strip() for e in f.notify_emails.split(",") if e.strip()]:
                _mail.send_form_submission(
                    addr,
                    form_title=f.title,
                    municipality_name=municipality_name,
                    data=data,
                )

    return jsonify({"success": True})


@api_bp.route("/procedures")
def list_procedures():
    items = (
        ProcedureType.query
        .filter_by(is_active=True)
        .order_by(ProcedureType.is_featured.desc(), ProcedureType.order_index.asc(), ProcedureType.title.asc())
        .all()
    )
    return jsonify({"items": [item.to_public_dict() for item in items]})


@api_bp.route("/procedures/<slug>")
def get_procedure(slug):
    item = ProcedureType.query.filter_by(slug=slug, is_active=True).first_or_404()
    return jsonify({"procedure": item.to_public_dict()})


@api_bp.route("/procedures/submit", methods=["POST"])
def submit_procedure():
    procedure_slug = (request.form.get("procedure_slug") or "").strip()
    procedure = ProcedureType.query.filter_by(slug=procedure_slug, is_active=True).first_or_404()

    applicant_name = (request.form.get("applicant_name") or "").strip()
    applicant_email = (request.form.get("applicant_email") or "").strip()
    applicant_phone = (request.form.get("applicant_phone") or "").strip() or None
    applicant_address = (request.form.get("applicant_address") or "").strip() or None
    document_number = (request.form.get("document_number") or "").strip() or None
    if not applicant_name or not applicant_email:
        return jsonify({"ok": False, "message": "Nombre y email son obligatorios."}), 400

    raw_payload = request.form.get("payload_json") or "{}"
    try:
        payload = json.loads(raw_payload)
        if not isinstance(payload, dict):
            raise ValueError()
    except Exception:
        return jsonify({"ok": False, "message": "Datos del formulario inválidos."}), 400

    attachments = []
    for index, document_name in enumerate(procedure.required_documents):
        field_name = procedure_document_field_name(document_name, index)
        file = request.files.get(field_name)
        if not file or not file.filename:
            return jsonify({"ok": False, "message": f"Falta adjuntar: {document_name}."}), 400
        try:
            upload = minio_service.upload_stream(
                file,
                file.mimetype or "application/octet-stream",
                prefix="tramites",
                original_name=file.filename,
            )
        except Exception as exc:
            return jsonify({"ok": False, "message": f"No se pudo subir {document_name}: {exc}"}), 500

        asset = MediaAsset(
            filename=upload["object_name"],
            original_filename=file.filename,
            mime_type=file.mimetype or "application/octet-stream",
            size_bytes=upload["size"],
            public_url=upload["public_url"],
            is_public=False,
        )
        db.session.add(asset)
        db.session.flush()
        attachments.append(
            {
                "label": document_name,
                "field_name": field_name,
                "asset_id": asset.id,
                "filename": asset.original_filename,
                "mime_type": asset.mime_type,
                "public_url": asset.resolved_public_url,
            }
        )

    submission = ProcedureSubmission(
        procedure_type_id=procedure.id,
        applicant_name=applicant_name,
        applicant_email=applicant_email,
        applicant_phone=applicant_phone,
        applicant_address=applicant_address,
        document_number=document_number,
        payload_json=payload,
        attachments_json=attachments,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string,
    )
    db.session.add(submission)
    db.session.commit()

    # Send confirmation email with tracking code
    try:
        site = SiteSettings.get_settings()
        send_procedure_received(
            applicant_email,
            applicant_name=applicant_name,
            municipality_name=site.name or "Municipio",
            procedure_title=procedure.title,
            tracking_code=submission.tracking_code,
        )
    except Exception:
        pass  # Non-blocking

    return jsonify(
        {
            "ok": True,
            "message": "Solicitud enviada correctamente.",
            "receipt": submission.to_public_receipt(),
        }
    )


@api_bp.route("/procedures/track/<tracking_code>")
def track_procedure(tracking_code: str):
    code = tracking_code.upper().strip()
    submission = ProcedureSubmission.query.filter_by(tracking_code=code).first()
    if not submission:
        return jsonify({"ok": False, "message": "Código de seguimiento no encontrado."}), 404
    return jsonify({"ok": True, "submission": submission.to_public_receipt()})


# ---------------------------------------------------------------------------
# Transparencia — Acceso a la Información Pública
# ---------------------------------------------------------------------------

def _generate_transparency_ref() -> str:
    """Genera un número de referencia único tipo TR-YYYYMM-XXXX."""
    prefix = datetime.utcnow().strftime("TR-%Y%m-")
    suffix = uuid.uuid4().hex[:6].upper()
    return f"{prefix}{suffix}"


@api_bp.route("/transparency/submit", methods=["POST"])
def submit_transparency_request():
    data = request.get_json(silent=True) or {}

    required = ["requesterType", "fullNameOrBusinessName", "identifier", "address", "email",
                "preferredResponseChannel", "requestedInformation", "municipality", "acceptedTerms"]
    for field in required:
        if not data.get(field):
            return jsonify({"ok": False, "message": f"El campo '{field}' es obligatorio."}), 400

    info = (data.get("requestedInformation") or "").strip()
    if len(info) < 20:
        return jsonify({"ok": False, "message": "La descripción de la información solicitada es demasiado corta (mínimo 20 caracteres)."}), 400
    if len(info) > 4000:
        return jsonify({"ok": False, "message": "La descripción excede el máximo permitido (4000 caracteres)."}), 400

    ref = _generate_transparency_ref()

    tr = TransparencyRequest(
        reference_number=ref,
        requester_type=(data.get("requesterType") or "").strip(),
        full_name=(data.get("fullNameOrBusinessName") or "").strip(),
        identifier=(data.get("identifier") or "").strip(),
        address=(data.get("address") or "").strip(),
        email=(data.get("email") or "").strip(),
        phone=(data.get("phone") or "").strip() or None,
        preferred_response_channel=(data.get("preferredResponseChannel") or "").strip(),
        requested_information=info,
        additional_location_data=(data.get("additionalLocationData") or "").strip() or None,
        preferred_format=(data.get("preferredFormat") or "").strip() or None,
        municipality=(data.get("municipality") or "").strip(),
        accepted_terms=bool(data.get("acceptedTerms")),
        ip_address=request.remote_addr,
    )
    db.session.add(tr)
    db.session.commit()

    # Notificación interna y acuse al solicitante (silencioso si falla)
    try:
        site = SiteSettings.get_settings()
        municipality_name = site.name or tr.municipality or "Municipio"

        if site.email:
            send_email(
                subject=f"[Transparencia] Nueva solicitud {ref}",
                recipients=[site.email],
                text_body=(
                    f"Se recibió una nueva solicitud de acceso a la información pública.\n\n"
                    f"Número de referencia: {ref}\n"
                    f"Solicitante: {tr.full_name}\n"
                    f"Correo: {tr.email}\n"
                    f"Información solicitada:\n{tr.requested_information[:500]}\n\n"
                    f"Revisá el panel administrativo para gestionar la solicitud."
                ),
            )

        send_email(
            subject=(
                f"Recibimos tu solicitud de acceso a la información pública"
                f" — {municipality_name}"
            ),
            recipients=[tr.email],
            text_body=(
                f"Hola {tr.full_name},\n\n"
                f"Recibimos correctamente tu solicitud de acceso a la información pública."
                f" A continuación te enviamos una copia de los datos registrados.\n\n"
                f"Número de referencia: {ref}\n"
                f"Municipio: {tr.municipality}\n"
                f"Tipo de solicitante: {tr.requester_type}\n"
                f"Documento / identificador: {tr.identifier}\n"
                f"Domicilio: {tr.address}\n"
                f"Correo electrónico: {tr.email}\n"
                f"Teléfono: {tr.phone or '-'}\n"
                f"Canal de respuesta preferido: {tr.preferred_response_channel}\n"
                f"Formato preferido: {tr.preferred_format or 'Sin preferencia'}\n"
                f"Datos adicionales: {tr.additional_location_data or '-'}\n\n"
                f"Información solicitada:\n{tr.requested_information}\n\n"
                f"Tu solicitud será tramitada conforme a la Ley N.º 18.381."
                f" Conservá este correo como comprobante de recepción."
            ),
        )
    except Exception:
        pass

    return jsonify({
        "ok": True,
        "message": "Su solicitud fue enviada correctamente.",
        "referenceNumber": ref,
    })
