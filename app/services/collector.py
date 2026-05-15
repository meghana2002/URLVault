"""HTTP collector — fetches headers, cookies, and page source for a URL.

Uses an async `httpx.AsyncClient` so a single FastAPI worker can handle
many concurrent collections without blocking the event loop.
"""
from __future__ import annotations

import logging
from typing import Optional

import httpx

from app.config import Settings, get_settings
from app.models.metadata import MetadataRecord

logger = logging.getLogger(__name__)


class HttpMetadataCollector:
    """Asynchronously collects HTTP metadata for a given URL."""

    def __init__(
        self,
        client: Optional[httpx.AsyncClient] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        self._settings = settings or get_settings()
        self._client = client  # If None, a transient client is created per call.

    async def collect(self, url: str) -> MetadataRecord:
        """Fetch a URL and return a populated `MetadataRecord`.

        Network/HTTP errors are *captured* (not raised) and persisted in the
        `error` field so failures stay observable in the inventory.
        """
        timeout = httpx.Timeout(self._settings.http_timeout_seconds)
        headers = {"User-Agent": self._settings.http_user_agent}

        async def _do(client: httpx.AsyncClient) -> MetadataRecord:
            try:
                response = await client.get(url, headers=headers)
            except httpx.HTTPError as exc:
                logger.warning("Collection failed for %s: %s", url, exc)
                return MetadataRecord(url=url, error=str(exc))

            return MetadataRecord(
                url=url,
                status_code=response.status_code,
                headers={k.lower(): v for k, v in response.headers.items()},
                cookies=dict(response.cookies),
                page_source=response.text,
            )

        if self._client is not None:
            return await _do(self._client)

        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            max_redirects=self._settings.http_max_redirects,
        ) as client:
            return await _do(client)