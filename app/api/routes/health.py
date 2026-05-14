"""Liveness / readiness endpoints."""
from fastapi import APIRouter, status
from pymongo.errors import PyMongoError

from app.db.mongo import mongo
from app.models.metadata import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health() -> HealthResponse:
    """Return service health, including a live MongoDB ping."""
    db_status = "ok"
    try:
        await mongo.client.admin.command("ping")
    except (PyMongoError, RuntimeError) as exc:
        db_status = f"unavailable: {exc}"

    overall = "ok" if db_status == "ok" else "degraded"
    return HealthResponse(status=overall, database=db_status)