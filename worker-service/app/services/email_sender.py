from __future__ import annotations

from abc import ABC, abstractmethod

import resend

from app.schemas import SendEmailPayload


class EmailSender(ABC):
    @abstractmethod
    def send(self, payload: SendEmailPayload) -> dict[str, bool]:
        raise NotImplementedError


class FakeEmailSender(EmailSender):
    def send(self, payload: SendEmailPayload) -> dict[str, bool]:
        return {"delivered": True}


class ResendEmailSender(EmailSender):
    api_url = "https://api.resend.com/emails"

    def __init__(
        self,
        api_key: str,
        from_email: str = "onboarding@resend.dev",
        from_name: str = "Task Flow",
    ) -> None:
        self.from_email = from_email
        self.from_name = from_name
        resend.api_key = api_key

    @property
    def from_address(self) -> str:
        return f"{self.from_name} <{self.from_email}>"

    def send(self, payload: SendEmailPayload) -> dict[str, bool | str]:
        try:
            response_payload = resend.Emails.send(
                {
                    "from": self.from_address,
                    "to": [str(payload.to)],
                    "subject": payload.subject,
                    "html": f"<p>{payload.body}</p>",
                    "text": payload.body,
                }
            )
        except Exception as exc:
            raise RuntimeError(f"Resend request failed: {exc}") from exc

        return {
            "delivered": True,
            "email_id": response_payload["id"],
        }


def build_email_sender(
    mode: str,
    resend_api_key: str | None = None,
    resend_from_email: str = "onboarding@resend.dev",
    resend_from_name: str = "Task Flow",
) -> EmailSender:
    if mode == "fake":
        return FakeEmailSender()
    if mode == "resend":
        if not resend_api_key:
            raise ValueError("RESEND_API_KEY is required when EMAIL_PROVIDER_MODE=resend")
        return ResendEmailSender(
            api_key=resend_api_key,
            from_email=resend_from_email,
            from_name=resend_from_name,
        )
    raise ValueError(f"Unsupported EMAIL_PROVIDER_MODE: {mode}")
