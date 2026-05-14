"""FastAPI application entry point."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app import __version__
from app.api.routes import health, metadata
from app.config import get_settings
from app.core.exceptions import DatabaseUnavailableError, MetadataServiceError
from app.core.logging import configure_logging
from app.db.indexes import ensure_indexes
from app.db.mongo import mongo

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup/shutdown."""
    configure_logging()
    settings = get_settings()
    logger.info("Starting %s (env=%s)", settings.app_name, settings.app_env)

    await mongo.connect(settings)
    await ensure_indexes()

    try:
        yield
    finally:
        await mongo.disconnect()
        logger.info("Shutdown complete.")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title="HTTP Metadata Inventory Service",
        description=(
            "Collects HTTP headers, cookies, and page source for any URL "
            "and stores them in MongoDB. Cache-miss collection happens "
            "asynchronously via FastAPI background tasks."
        ),
        version=__version__,
        lifespan=lifespan,
    )

    app.include_router(health.router)
    app.include_router(metadata.router, prefix=settings.api_v1_prefix)

    @app.exception_handler(DatabaseUnavailableError)
    async def _db_unavailable(_: Request, exc: DatabaseUnavailableError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": str(exc)},
        )

    @app.exception_handler(MetadataServiceError)
    async def _service_error(_: Request, exc: MetadataServiceError) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": str(exc)},
        )

    return app


app = create_app()