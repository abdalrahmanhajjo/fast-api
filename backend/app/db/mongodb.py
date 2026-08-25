"""MongoDB connection lifecycle.

`connect_to_mongo` is called once on application startup and
`close_mongo_connection` on shutdown. Tests bypass both and call
`init_models` directly with an in-memory client.
"""

import logging
from typing import Optional

from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient

from app.core.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

# Every Beanie Document the app owns. Add new models here.
DOCUMENT_MODELS = [User]

_client: Optional[AsyncIOMotorClient] = None


async def init_models(database) -> None:
    """Bind the Beanie document models to a database handle."""
    await init_beanie(database=database, document_models=DOCUMENT_MODELS)


async def connect_to_mongo() -> None:
    """Open the Motor client and initialise Beanie."""
    global _client
    _client = AsyncIOMotorClient(settings.MONGODB_URI, uuidRepresentation="standard")
    await init_models(_client[settings.MONGODB_DB_NAME])
    logger.info("Connected to MongoDB database %r", settings.MONGODB_DB_NAME)


async def close_mongo_connection() -> None:
    """Close the Motor client."""
    global _client
    if _client is not None:
        _client.close()
        _client = None
        logger.info("MongoDB connection closed")


def get_client() -> Optional[AsyncIOMotorClient]:
    return _client
