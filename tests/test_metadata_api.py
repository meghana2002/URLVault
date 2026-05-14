"""Integration tests for the metadata API."""
import asyncio

import pytest


@pytest.mark.asyncio
async def test_post_creates_record(client):
    resp = await client.post(
        "/api/v1/metadata",
        json={"url": "https://example.com/post-test"},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["url"] == "https://example.com/post-test"
    assert body["status_code"] == 200
    assert "headers" in body and body["headers"]
    assert body["page_source"].startswith("<!doctype html>")


@pytest.mark.asyncio
async def test_post_rejects_invalid_url(client):
    resp = await client.post("/api/v1/metadata", json={"url": "not-a-url"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_returns_record_when_present(client):
    url = "https://example.com/get-hit"
    await client.post("/api/v1/metadata", json={"url": url})

    resp = await client.get("/api/v1/metadata", params={"url": url})
    assert resp.status_code == 200
    body = resp.json()
    assert body["url"] == url
    assert body["status_code"] == 200


@pytest.mark.asyncio
async def test_get_returns_202_on_cache_miss_and_collects_in_background(client):
    url = "https://example.com/get-miss"

    resp = await client.get("/api/v1/metadata", params={"url": url})
    assert resp.status_code == 202
    body = resp.json()
    assert body["url"] == url
    assert "scheduled" in body["detail"].lower()

    for _ in range(20):
        await asyncio.sleep(0.05)
        follow_up = await client.get("/api/v1/metadata", params={"url": url})
        if follow_up.status_code == 200:
            assert follow_up.json()["url"] == url
            break
    else:
        pytest.fail("Background collection did not persist the record in time.")


@pytest.mark.asyncio
async def test_get_validates_url(client):
    resp = await client.get("/api/v1/metadata", params={"url": "garbage"})
    assert resp.status_code == 422