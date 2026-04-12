from __future__ import annotations

from app.schemas import SendEmailPayload
from app.services.email_sender import EmailSender


def handle_send_email(payload: SendEmailPayload, email_sender: EmailSender) -> dict[str, bool]:
    return email_sender.send(payload)
