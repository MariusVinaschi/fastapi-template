"""
Tests for API startup validation of CLERK_FRONTEND_API_URL.

The check lives in create_application() (app/api/main.py), not on the shared
Settings model, because Settings is also imported by the worker and migrations
images, which don't need Clerk configured.
"""

import pytest

from app.api.main import create_application
from app.infrastructure.config import settings


def test_create_application_raises_when_clerk_frontend_api_url_is_blank(monkeypatch):
    monkeypatch.setattr(settings, "CLERK_FRONTEND_API_URL", "")

    with pytest.raises(ValueError, match="CLERK_FRONTEND_API_URL"):
        create_application()


def test_create_application_raises_when_clerk_frontend_api_url_is_whitespace(monkeypatch):
    monkeypatch.setattr(settings, "CLERK_FRONTEND_API_URL", "   ")

    with pytest.raises(ValueError, match="CLERK_FRONTEND_API_URL"):
        create_application()


def test_create_application_succeeds_with_valid_clerk_frontend_api_url(monkeypatch):
    monkeypatch.setattr(settings, "CLERK_FRONTEND_API_URL", "https://valid.clerk.accounts.dev")

    app = create_application()

    assert app is not None
