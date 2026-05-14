"""Unit tests for the HTTP collector."""
import pytest

from app.services.collector import HttpMetadataCollector


@pytest.mark.asyncio
async def test_collector_returns_populated_record():
    collector = HttpMetadataCollector()
    record = await collector.collect("https://example.com/")
    assert record.url == "https://example.com/"
    assert record.status_code == 200
    assert record.headers.get("content-type", "").startswith("text/html")
    assert "Mock for" in (record.page_source or "")
    assert record.error is None


@pytest.mark.asyncio
async def test_collector_records_http_error_status():
    collector = HttpMetadataCollector()
    record = await collector.collect("https://example.com/boom")
    assert record.status_code == 500
    assert record.page_source == "boom"
    assert record.error is None


@pytest.mark.asyncio
async def test_collector_captures_connection_error():
    collector = HttpMetadataCollector()
    record = await collector.collect("https://errors.test/")
    assert record.status_code is None
    assert record.error is not None
    assert "simulated connection error" in record.error