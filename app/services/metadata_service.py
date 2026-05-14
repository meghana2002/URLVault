"""Business logic for the metadata inventory.

The route layer should never touch the repository or collector directly —
it talks to this service. That keeps transport concerns separate and makes
the logic trivially unit-testable.
"""
from __future__ import annotations

import logging
from typing import Optional

from app.models.metadata import MetadataRecord
from app.repositories.metadata_repository import MetadataRepository
from app.services.collector import HttpMetadataCollector

logger = logging.getLogger(__name__)


class MetadataService:
    """Orchestrates collection + persistence of HTTP metadata."""

    def __init__(
        self,
        repository: MetadataRepository,
        collector: HttpMetadataCollector,
    ) -> None:
        self._repository = repository
        self._collector = collector

    async def get(self, url: str) -> Optional[MetadataRecord]:
        return await self._repository.find_by_url(url)

    async def collect_and_store(self, url: str) -> MetadataRecord:
        """Fetch the URL synchronously and persist the result (used by POST)."""
        record = await self._collector.collect(url)
        return await self._repository.upsert(record)

    async def background_collect(self, url: str) -> None:
        """Entrypoint scheduled by FastAPI `BackgroundTasks` on cache miss.

        Wraps `collect_and_store` and swallows any unexpected exception so a
        broken background task can never crash the worker process.
        """
        try:
            logger.info("Background collection started for %s", url)
            await self.collect_and_store(url)
            logger.info("Background collection completed for %s", url)
        except Exception:  # noqa: BLE001 - we *want* to absorb here
            logger.exception("Background collection failed for %s", url)