"""MongoDB connection lifecycle management.

Uses Motor (async PyMongo) and retries connection on startup with
exponential backoff so the API stays resilient to database boot delays.
"""
from __future__ import annotations

import asyncio
import logging
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from app.config import Settings, get_settings
from app.core.exceptions import DatabaseUnavailableError

logger = logging.getLogger(__name__)


class MongoConnection:
    """Encapsulates a Motor client and exposes the configured database/collection."""

    def __init__(self) -> None:
        self._client: Optional[AsyncIOMotorClient] = None
        self._db: Optional[AsyncIOMotorDatabase] = None

    @property
    def client(self) -> AsyncIOMotorClient:
        if self._client is None:
            raise RuntimeError("Mongo client not initialised. Call connect() first.")
        return self._client

    @property
    def database(self) -> AsyncIOMotorDatabase:
        if self._db is None:
            raise RuntimeError("Mongo database not initialised. Call connect() first.")
        return self._db

    def collection(self, name: str) -> AsyncIOMotorCollection:
        return self.database[name]

    async def connect(self, settings: Settings | None = None) -> None:
        """Open the Motor client and ping the server with retry/backoff."""
        settings = settings or get_settings()

        self._client = AsyncIOMotorClient(
            settings.mongo_uri,
            maxPoolSize=settings.mongo_max_pool_size,
            serverSelectionTimeoutMS=2000,
            uuidRepresentation="standard",
        )
        self._db = self._client[settings.mongo_db]

        deadline = settings.startup_retry_seconds
        delay = 0.5
        elapsed = 0.0
        last_error: Exception | None = None

        while elapsed < deadline:
            try:
                await self._client.admin.command("ping")
                logger.info("Connected to MongoDB at %s", settings.mongo_uri)
                return
            except PyMongoError as exc:  # pragma: no cover - timing dependent
                last_error = exc
                logger.warning("MongoDB not ready (%s). Retrying in %.1fs...", exc, delay)
                await asyncio.sleep(delay)
                elapsed += delay
                delay = min(delay * 2, 5.0)

        raise DatabaseUnavailableError(
            f"Could not connect to MongoDB within {deadline}s: {last_error}"
        )

    async def disconnect(self) -> None:
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            logger.info("Disconnected from MongoDB")


mongo = MongoConnection()