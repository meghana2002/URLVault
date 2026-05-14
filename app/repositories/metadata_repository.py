"""Persistence layer for metadata records.

This is the **only** module that talks to MongoDB. Swapping the data store
later means replacing this file — services and routes stay untouched.
"""
from __future__ import annotations

import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorCollection

from app.models.metadata import MetadataRecord, serialize_record

logger = logging.getLogger(__name__)


class MetadataRepository:
    """CRUD operations for metadata documents."""

    def __init__(self, collection: AsyncIOMotorCollection) -> None:
        self._collection = collection

    async def find_by_url(self, url: str) -> Optional[MetadataRecord]:
        doc = await self._collection.find_one({"url": url})
        return serialize_record(doc) if doc else None

    async def exists(self, url: str) -> bool:
        return (await self._collection.count_documents({"url": url}, limit=1)) > 0

    async def upsert(self, record: MetadataRecord) -> MetadataRecord:
        """Insert or overwrite a record keyed by `url`."""
        payload = record.model_dump(mode="json")
        await self._collection.update_one(
            {"url": record.url},
            {"$set": payload},
            upsert=True,
        )
        logger.debug("Upserted metadata for url=%s", record.url)
        return record

    async def delete_by_url(self, url: str) -> bool:
        result = await self._collection.delete_one({"url": url})
        return result.deleted_count > 0