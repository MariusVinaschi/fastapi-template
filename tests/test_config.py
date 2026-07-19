"""Clerk is optional at API startup; create_application() must always succeed."""

from app.api.main import create_application
from app.infrastructure.config import settings


def test_create_application_succeeds_when_clerk_frontend_api_url_is_blank(monkeypatch):
    monkeypatch.setattr(settings, "CLERK_FRONTEND_API_URL", "")

    app = create_application()

    assert app is not None


def test_create_application_succeeds_when_clerk_frontend_api_url_is_whitespace(monkeypatch):
    monkeypatch.setattr(settings, "CLERK_FRONTEND_API_URL", "   ")

    app = create_application()

    assert app is not None


def test_create_application_succeeds_with_valid_clerk_frontend_api_url(monkeypatch):
    monkeypatch.setattr(settings, "CLERK_FRONTEND_API_URL", "https://valid.clerk.accounts.dev")

    app = create_application()

    assert app is not None


def test_create_application_succeeds_when_clerk_webhook_secret_is_blank(monkeypatch):
    monkeypatch.setattr(settings, "CLERK_WEBHOOK_SECRET", "")

    app = create_application()

    assert app is not None


def test_create_application_succeeds_with_no_clerk_configuration_at_all(monkeypatch):
    """The API-key-only deployment scenario: neither Clerk setting is configured."""
    monkeypatch.setattr(settings, "CLERK_FRONTEND_API_URL", "")
    monkeypatch.setattr(settings, "CLERK_WEBHOOK_SECRET", "")

    app = create_application()

    assert app is not None
