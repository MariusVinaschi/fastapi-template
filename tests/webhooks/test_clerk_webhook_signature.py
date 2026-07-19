"""
CLERK_WEBHOOK_SECRET is optional (defaults to ""), so the API can start without
Clerk configured at all. Receiving a webhook while it's unset must fail clearly
at request time rather than crashing with the svix library's raw RuntimeError.
"""

import pytest
from fastapi import FastAPI
from httpx import AsyncClient


@pytest.mark.anyio
async def test_clerk_webhook_returns_503_when_secret_is_blank(client: AsyncClient, app: FastAPI, monkeypatch):
    from app.infrastructure.config import settings

    monkeypatch.setattr(settings, "CLERK_WEBHOOK_SECRET", "")

    response = await client.post("/webhooks/clerk", json={"type": "user.created", "data": {}})

    assert response.status_code == 503
    assert "not configured" in response.json()["detail"]


@pytest.mark.anyio
async def test_clerk_webhook_returns_400_on_invalid_signature_when_configured(
    client: AsyncClient, app: FastAPI, monkeypatch
):
    from app.infrastructure.config import settings

    monkeypatch.setattr(settings, "CLERK_WEBHOOK_SECRET", "whsec_dGVzdC1jbGVyay13ZWJob29rLXNlY3JldA==")

    response = await client.post("/webhooks/clerk", json={"type": "user.created", "data": {}})

    assert response.status_code == 400
