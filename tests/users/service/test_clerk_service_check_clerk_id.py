import pytest

from app.domains.users.service import ClerkUserService


@pytest.mark.asyncio
async def test_check_clerk_id():
    clerk_id = "123"
    data = {
        "id": clerk_id,
    }
    find_clerk_id = ClerkUserService._check_clerk_id(data)
    assert clerk_id is not None
    assert find_clerk_id == clerk_id


@pytest.mark.asyncio
async def test_check_clerk_id_missing():
    data = {
        "id": None,
    }
    with pytest.raises(ValueError):
        ClerkUserService._check_clerk_id(data)
