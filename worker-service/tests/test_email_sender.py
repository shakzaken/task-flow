import pytest

from app.schemas import SendEmailPayload
from app.services.email_sender import FakeEmailSender, ResendEmailSender, build_email_sender


def test_build_email_sender_returns_fake_sender() -> None:
    sender = build_email_sender("fake")

    assert isinstance(sender, FakeEmailSender)


def test_build_email_sender_requires_api_key_for_resend() -> None:
    with pytest.raises(ValueError, match="RESEND_API_KEY"):
        build_email_sender("resend")


def test_resend_email_sender_posts_to_resend(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_payload = {}

    def fake_send(payload: dict[str, object]) -> dict[str, str]:
        captured_payload["value"] = payload
        return {"id": "email_123"}

    monkeypatch.setattr("app.services.email_sender.resend.Emails.send", fake_send)

    sender = ResendEmailSender(
        api_key="re_test_key",
        from_email="onboarding@resend.dev",
        from_name="Task Flow",
    )

    result = sender.send(
        SendEmailPayload(
            to="shakzaken@gmail.com",
            subject="Worker service test",
            body="This is a Resend integration test.",
        )
    )

    assert result == {"delivered": True, "email_id": "email_123"}
    assert captured_payload["value"] == {
        "from": "Task Flow <onboarding@resend.dev>",
        "to": ["shakzaken@gmail.com"],
        "subject": "Worker service test",
        "html": "<p>This is a Resend integration test.</p>",
        "text": "This is a Resend integration test.",
    }
