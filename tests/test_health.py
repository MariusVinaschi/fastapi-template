import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"health": "UP", "testing": False}
