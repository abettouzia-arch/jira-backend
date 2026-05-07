"""MongoDB client utilities for shared database access."""

import logging
import os
from functools import lru_cache

from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

logger = logging.getLogger(__name__)

DEFAULT_MONGO_URI = "mongodb://docker.itspectrum.fr:27017/jira_migration"


@lru_cache(maxsize=1)
def get_mongo_client() -> MongoClient:
    """Create and cache a MongoDB client instance."""
    mongo_uri = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
    logger.info("Using MongoDB URI: %s", mongo_uri)
    return MongoClient(mongo_uri)


def get_mongo_db():
    """Return the configured MongoDB database instance."""
    mongo_uri = os.getenv("MONGO_URI", DEFAULT_MONGO_URI)
    db_name = mongo_uri.rsplit("/", 1)[-1] or "jira_migration"
    client = get_mongo_client()
    return client[db_name]
