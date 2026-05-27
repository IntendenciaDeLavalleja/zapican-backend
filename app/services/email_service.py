"""Servicio de envío de mails (Flask-Mail) asíncrono."""
from __future__ import annotations

import logging
from threading import Thread

from flask import current_app, render_template
from flask_mail import Message

from app.extensions import mail

logger = logging.getLogger(__name__)


def _send_async(app, msg: Message) -> None:
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as exc:
            logger.warning("Mail send fallo: %s", exc)


def send_email(subject: str, recipients: list[str], *, text_body: str = "",
               html_body: str | None = None, sender: str | None = None) -> None:
    app = current_app._get_current_object()
    msg = Message(
        subject=subject,
        recipients=recipients,
        sender=sender or app.config.get("MAIL_DEFAULT_SENDER"),
        body=text_body or "",
        html=html_body,
    )
    Thread(target=_send_async, args=(app, msg), daemon=True).start()


def send_2fa_code(to_email: str, code: str) -> None:
    html = render_template("emails/2fa_code.html", code=code)
    send_email(
        "[Lavalleja CMS] Codigo de verificacion",
        [to_email],
        text_body=f"Tu codigo de verificacion es: {code}\nValido por 10 minutos.",
        html_body=html,
    )


def send_contact_received(to_email: str, *, municipality_name: str, subject: str,
                          sender_name: str = "", sender_email: str = "",
                          message: str = "") -> None:
    html = render_template(
        "emails/contact_received.html",
        municipality_name=municipality_name,
        subject=subject,
        sender_name=sender_name,
        sender_email=sender_email,
        message=message,
    )
    send_email(
        f"Nuevo mensaje de contacto — {municipality_name}",
        [to_email],
        text_body=f"Nuevo mensaje de {sender_name} <{sender_email}>: {subject}",
        html_body=html,
    )


def send_contact_confirmation(to_email: str, *, name: str, municipality_name: str,
                               subject: str) -> None:
    html = render_template(
        "emails/contact_confirmation.html",
        name=name,
        municipality_name=municipality_name,
        subject=subject,
    )
    send_email(
        f"Recibimos tu mensaje — {municipality_name}",
        [to_email],
        text_body=(
            f"Hola {name},\n\n"
            f"Recibimos tu mensaje \"{subject}\" correctamente. "
            f"El equipo de {municipality_name} te responderá a la brevedad.\n\n"
            f"Gracias por comunicarte."
        ),
        html_body=html,
    )


def send_form_submission(to_email: str, *, form_title: str, municipality_name: str,
                         data: dict) -> None:
    html = render_template(
        "emails/form_submission.html",
        form_title=form_title,
        municipality_name=municipality_name,
        data=data,
    )
    send_email(
        f"Nueva respuesta - {form_title} ({municipality_name})",
        [to_email],
        text_body=f"Nueva respuesta al formulario {form_title}.",
        html_body=html,
    )


def send_procedure_received(to_email: str, *, applicant_name: str, municipality_name: str,
                             procedure_title: str, tracking_code: str) -> None:
    html = render_template(
        "emails/procedure_received.html",
        applicant_name=applicant_name,
        municipality_name=municipality_name,
        procedure_title=procedure_title,
        tracking_code=tracking_code,
    )
    send_email(
        f"Solicitud de trámite recibida — {municipality_name}",
        [to_email],
        text_body=(
            f"Hola {applicant_name},\n\n"
            f"Recibimos tu solicitud de trámite \"{procedure_title}\".\n"
            f"Tu código de seguimiento es: {tracking_code}\n\n"
            f"Podés usarlo para consultar el estado en el sitio de {municipality_name}.\n\n"
            f"Gracias."
        ),
        html_body=html,
    )
