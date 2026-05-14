"""FastAPI dependency providers — the only place wiring happens."""
from __future__ import annotations

from app.config import get_settings
from app.db.mongo import mongo
from app.repositories.metadata_repository import MetadataRepository
from app.services.collector import HttpMetadataCollector
from app.services.metadata_service import MetadataService


def get_repository() -> MetadataRepository:
    settings = get_settings()
    return MetadataRepository(mongo.collection(settings.mongo_collection))


def get_collector() -> HttpMetadataCollector:
    return HttpMetadataCollector()


def get_metadata_service() -> MetadataService:
    return MetadataService(repository=get_repository(), collector=get_collector())