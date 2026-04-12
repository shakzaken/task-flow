from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas import SendEmailPayload


class EmailSender(ABC):
    @abstractmethod
    def send(self, payload: SendEmailPayload) -> dict[str, bool]:
        raise NotImplementedError


class FakeEmailSender(EmailSender):
    def send(self, payload: SendEmailPayload) -> dict[str, bool]:
        return {"delivered": True}


def build_email_sender(mode: str) -> EmailSender:
    if mode == "fake":
        return FakeEmailSender()
    raise ValueError(f"Unsupported EMAIL_PROVIDER_MODE: {mode}")
