"""Centralised logging configuration."""
import logging
import sys

from app.config import get_settings


def configure_logging() -> None:
    """Configure the root logger based on application settings."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    # Quiet down noisy third-party loggers
    for noisy in ("httpx", "httpcore", "pymongo", "uvicorn.access"):
        logging.getLogger(noisy).setLevel(max(level, logging.WARNING))