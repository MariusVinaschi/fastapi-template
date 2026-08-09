"""Application config: the app always builds, and auth transport is settings-driven."""

from app.api.main import create_application
from app.infrastructure.config import settings


def test_create_application_succeeds():
    assert create_application() is not None


def test_auth_token_locations_parsing(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_TOKEN_LOCATION", "headers,cookies")
    assert settings.AUTH_TOKEN_LOCATIONS == ["headers", "cookies"]


def test_auth_cookie_csrf_protect_enabled_only_with_cookies(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_TOKEN_LOCATION", "headers")
    assert settings.AUTH_COOKIE_CSRF_PROTECT is False

    monkeypatch.setattr(settings, "AUTH_TOKEN_LOCATION", "headers,cookies")
    assert settings.AUTH_COOKIE_CSRF_PROTECT is True


def test_auth_jwt_signing_key_falls_back_to_secret_key(monkeypatch):
    monkeypatch.setattr(settings, "AUTH_JWT_SECRET_KEY", "")
    monkeypatch.setattr(settings, "SECRET_KEY", "the-secret")
    assert settings.AUTH_JWT_SIGNING_KEY == "the-secret"

    monkeypatch.setattr(settings, "AUTH_JWT_SECRET_KEY", "dedicated-jwt-key")
    assert settings.AUTH_JWT_SIGNING_KEY == "dedicated-jwt-key"
