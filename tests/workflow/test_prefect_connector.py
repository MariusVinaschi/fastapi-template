import pytest

from app.infrastructure.database import SqlAlchemyConnector, _load_prefect_connector

pytestmark = pytest.mark.anyio


async def test_missing_prefect_block_is_reported(monkeypatch):
    monkeypatch.setattr(SqlAlchemyConnector, "load", lambda _: None)
    with pytest.raises(ValueError, match="not found"):
        await _load_prefect_connector("missing")


async def test_empty_loaded_prefect_block_is_reported(monkeypatch):
    async def load(_):
        return None

    monkeypatch.setattr(SqlAlchemyConnector, "load", load)
    with pytest.raises(ValueError, match="failed to load"):
        await _load_prefect_connector("empty")


async def test_loaded_prefect_block_is_returned(monkeypatch):
    connector = object()

    async def load(_):
        return connector

    monkeypatch.setattr(SqlAlchemyConnector, "load", load)
    assert await _load_prefect_connector("existing") is connector
