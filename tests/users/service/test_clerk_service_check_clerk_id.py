import pytest

from app.infrastructure.adapters.clerk import ClerkWebhookAdapter


@pytest.mark.anyio
async def test_check_clerk_id():
    clerk_id = "123"
    data = {
        "id": clerk_id,
    }
    find_clerk_id = ClerkWebhookAdapter._check_clerk_id(data)
    assert clerk_id is not None
    assert find_clerk_id == clerk_id


@pytest.mark.anyio
async def test_check_clerk_id_missing():
    data = {
        "id": None,
    }
    with pytest.raises(ValueError):
        ClerkWebhookAdapter._check_clerk_id(data)
