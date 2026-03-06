import pytest

from app.infrastructure.adapters.clerk import ClerkWebhookAdapter


@pytest.mark.anyio
async def test_extract_primary_email_single_email():
    email = "test@example.com"
    data = {
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": email},
        ],
    }
    primary_email = ClerkWebhookAdapter._extract_primary_email(data)
    assert primary_email is not None
    assert primary_email == email


@pytest.mark.anyio
async def test_extract_primary_email_multiple_emails(db_session):
    email = "test@example.com"
    data = {
        "primary_email_address_id": "123",
        "email_addresses": [
            {"id": "123", "email_address": email},
            {"id": "456", "email_address": "test2@example.com"},
        ],
    }
    primary_email = ClerkWebhookAdapter._extract_primary_email(data)
    assert primary_email is not None
    assert primary_email == email


@pytest.mark.anyio
async def test_extract_primary_email_multiple_emails_no_primary(db_session):
    data = {
        "primary_email_address_id": "123",
        "email_addresses": [],
    }
    with pytest.raises(ValueError):
        ClerkWebhookAdapter._extract_primary_email(data)
