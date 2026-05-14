"""MongoDB index management."""
import logging

from app.config import get_settings
from app.db.mongo import mongo

logger = logging.getLogger(__name__)


async def ensure_indexes() -> None:
    """Create required indexes idempotently on application start.

    A unique ascending index on `url` guarantees one record per URL and
    makes both reads and upserts logarithmic.
    """
    settings = get_settings()
    collection = mongo.collection(settings.mongo_collection)

    await collection.create_index("url", unique=True, name="uniq_url")
    await collection.create_index("collected_at", name="collected_at_idx")
    logger.info("Indexes ensured on collection '%s'", settings.mongo_collection)