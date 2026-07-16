"""
Tests for Settings startup validation.

These construct Settings directly with explicit kwargs (and _env_file=None) so the
real .env / .env.local files on disk cannot mask a missing CLERK_FRONTEND_API_URL.
"""

import pytest
from pydantic import ValidationError

from app.infrastructure.config import Settings


def test_blank_clerk_frontend_api_url_raises_when_not_testing():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            SECRET_KEY="x",
            CLERK_WEBHOOK_SECRET="y",
            CLERK_FRONTEND_API_URL="",
            TESTING=False,
        )


def test_whitespace_only_clerk_frontend_api_url_raises_when_not_testing():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            SECRET_KEY="x",
            CLERK_WEBHOOK_SECRET="y",
            CLERK_FRONTEND_API_URL="   ",
            TESTING=False,
        )


def test_blank_clerk_frontend_api_url_allowed_when_testing():
    settings = Settings(
        _env_file=None,
        SECRET_KEY="x",
        CLERK_WEBHOOK_SECRET="y",
        CLERK_FRONTEND_API_URL="",
        TESTING=True,
    )

    assert settings.CLERK_FRONTEND_API_URL == ""


def test_valid_clerk_frontend_api_url_passes_regardless_of_testing():
    for testing_flag in (True, False):
        settings = Settings(
            _env_file=None,
            SECRET_KEY="x",
            CLERK_WEBHOOK_SECRET="y",
            CLERK_FRONTEND_API_URL="https://valid.clerk.accounts.dev",
            TESTING=testing_flag,
        )

        assert settings.CLERK_FRONTEND_API_URL == "https://valid.clerk.accounts.dev"
