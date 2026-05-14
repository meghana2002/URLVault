"""Metadata HTTP endpoints (POST + GET)."""
from __future__ import annotations

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Response, status
from pydantic import HttpUrl

from app.api.deps import get_metadata_service
from app.core.exceptions import CollectionError
from app.models.metadata import (
    AcceptedResponse,
    MetadataCreateRequest,
    MetadataRecord,
)
from app.services.metadata_service import MetadataService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/metadata", tags=["metadata"])


@router.post(
    "",
    response_model=MetadataRecord,
    status_code=status.HTTP_201_CREATED,
    summary="Synchronously collect and store metadata for a URL.",
)
async def create_metadata(
    payload: MetadataCreateRequest,
    service: MetadataService = Depends(get_metadata_service),
) -> MetadataRecord:
    """Fetch headers/cookies/page source for the supplied URL and persist it.

    Returns the created record. If the URL was already indexed, it is
    refreshed (upsert).
    """
    url = str(payload.url)
    try:
        return await service.collect_and_store(url)
    except CollectionError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc


@router.get(
    "",
    summary="Retrieve metadata for a URL; queue background collection on miss.",
    responses={
        200: {"model": MetadataRecord, "description": "Record found."},
        202: {"model": AcceptedResponse, "description": "Collection scheduled."},
    },
)
async def get_metadata(
    response: Response,
    background_tasks: BackgroundTasks,
    url: HttpUrl = Query(..., description="The URL to look up."),
    service: MetadataService = Depends(get_metadata_service),
) -> MetadataRecord | AcceptedResponse:
    """Return the stored record, or accept the request and collect in the background.

    Background work is scheduled with FastAPI's `BackgroundTasks`, which
    runs the coroutine *after* the response is sent — fulfilling the
    "no self-HTTP loop, no blocking" architectural constraint.
    """
    url_str = str(url)
    record = await service.get(url_str)
    if record is not None:
        return record

    background_tasks.add_task(service.background_collect, url_str)
    response.status_code = status.HTTP_202_ACCEPTED
    return AcceptedResponse(
        detail="URL not in inventory. Collection scheduled in the background.",
        url=url_str,
    )