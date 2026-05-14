"""Pydantic schemas for transport and persistence layers."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class MetadataCreateRequest(BaseModel):
    """Inbound POST body."""
    url: HttpUrl = Field(..., description="Absolute HTTP/HTTPS URL to fetch.")


class MetadataRecord(BaseModel):
    """Canonical metadata document returned by the API and stored in MongoDB.

    Note: `_id` is intentionally omitted from the public model — MongoDB
    generates it internally; clients should treat `url` as the natural key.
    """
    model_config = ConfigDict(populate_by_name=True)

    url: str = Field(..., description="The fetched URL (also the natural key).")
    status_code: Optional[int] = Field(
        None, description="HTTP status returned by the origin server."
    )
    headers: dict[str, str] = Field(default_factory=dict)
    cookies: dict[str, str] = Field(default_factory=dict)
    page_source: Optional[str] = Field(
        None, description="Raw response body (decoded text)."
    )
    error: Optional[str] = Field(
        None, description="Populated when the collection attempt failed."
    )
    collected_at: datetime = Field(default_factory=_utcnow)


class AcceptedResponse(BaseModel):
    """Body returned with HTTP 202 when collection is queued."""
    detail: str
    url: str


class HealthResponse(BaseModel):
    status: str
    database: str


def serialize_record(doc: dict[str, Any]) -> MetadataRecord:
    """Convert a raw Mongo document to a Pydantic model (drops `_id`)."""
    doc = dict(doc)
    doc.pop("_id", None)
    return MetadataRecord.model_validate(doc)