"""
Clerk is optional at API startup: neither CLERK_FRONTEND_API_URL (JWT auth)
nor CLERK_WEBHOOK_SECRET (webhook receiving) are required for
create_application() to succeed, so API-key-only / local use works. Both
fail clearly at request time instead: JWT auth in VerifyAuth.jwks_client,
webhook receiving in _verify_webhook_signature.
"""

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
