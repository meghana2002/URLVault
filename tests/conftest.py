"""Shared pytest fixtures.

The test suite is hermetic: MongoDB is replaced with `mongomock-motor`,
and outbound HTTP is replaced with `httpx.MockTransport`. No network or
external services are required to run `pytest`.
"""
from __future__ import annotations

import os
from typing import AsyncIterator

import httpx
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from mongomock_motor import AsyncMongoMockClient

# Force test env vars before settings is imported anywhere.
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("MONGO_URI", "mongodb://localhost:27017")
os.environ.setdefault("MONGO_DB", "metadata_inventory_test")
os.environ.setdefault("STARTUP_RETRY_SECONDS", "2")

from app import main as main_module  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.db import mongo as mongo_module  # noqa: E402
from app.services import collector as collector_module  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def _patch_mongo(monkeypatch):
    """Replace the module-level `mongo` connection with an in-memory mock."""
    settings = get_settings()
    client = AsyncMongoMockClient()
    mongo_module.mongo._client = client  # type: ignore[attr-defined]
    mongo_module.mongo._db = client[settings.mongo_db]  # type: ignore[attr-defined]

    async def _noop_connect(*_a, **_kw):
        return None

    async def _noop_disconnect():
        return None

    monkeypatch.setattr(mongo_module.mongo, "connect", _noop_connect)
    monkeypatch.setattr(mongo_module.mongo, "disconnect", _noop_disconnect)

    yield

    await client[settings.mongo_db][settings.mongo_collection].delete_many({})


def _default_transport_handler(request: httpx.Request) -> httpx.Response:
    """Mock HTTP backend: returns a deterministic page for example.com,
    a 500 for `/boom`, and a connection error for `errors.test`."""
    host = request.url.host
    path = request.url.path

    if host == "errors.test":
        raise httpx.ConnectError("simulated connection error", request=request)

    if path == "/boom":
        return httpx.Response(500, text="boom")

    body = f"<!doctype html><html><body><h1>Mock for {request.url}</h1></body></html>"
    return httpx.Response(
        200,
        headers={"content-type": "text/html; charset=utf-8", "x-mock": "1"},
        text=body,
        extensions={},
    )


@pytest.fixture
def mock_transport() -> httpx.MockTransport:
    return httpx.MockTransport(_default_transport_handler)


@pytest.fixture(autouse=True)
def _patch_httpx(monkeypatch, mock_transport):
    """Patch the collector's httpx.AsyncClient to use a MockTransport."""
    original_async_client = httpx.AsyncClient

    def _factory(*args, **kwargs):
        kwargs["transport"] = mock_transport
        return original_async_client(*args, **kwargs)

    monkeypatch.setattr(collector_module.httpx, "AsyncClient", _factory)


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """Async HTTP client wired to the ASGI app (no real network)."""
    transport = ASGITransport(app=main_module.app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac