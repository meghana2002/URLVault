"""Unit tests for the repository layer."""
import pytest

from app.api.deps import get_repository
from app.models.metadata import MetadataRecord


@pytest.mark.asyncio
async def test_upsert_and_find():
    repo = get_repository()
    record = MetadataRecord(
        url="https://example.com/repo-test",
        status_code=200,
        headers={"x-test": "1"},
        cookies={},
        page_source="<html/>",
    )
    await repo.upsert(record)

    found = await repo.find_by_url("https://example.com/repo-test")
    assert found is not None
    assert found.status_code == 200
    assert found.headers["x-test"] == "1"


@pytest.mark.asyncio
async def test_exists_and_delete():
    repo = get_repository()
    url = "https://example.com/delete-me"
    await repo.upsert(MetadataRecord(url=url, status_code=200))

    assert await repo.exists(url) is True
    assert await repo.delete_by_url(url) is True
    assert await repo.exists(url) is False


@pytest.mark.asyncio
async def test_upsert_is_idempotent_on_url():
    repo = get_repository()
    url = "https://example.com/idem"
    await repo.upsert(MetadataRecord(url=url, status_code=200))
    await repo.upsert(MetadataRecord(url=url, status_code=201))

    found = await repo.find_by_url(url)
    assert found is not None
    assert found.status_code == 201