"""Background synchronization of learned component knowledge."""

import logging
import os
import threading

import requests

logger = logging.getLogger(__name__)

AUTO_SYNC_ENABLED = os.getenv("LEARNED_KNOWLEDGE_AUTO_SYNC_ENABLED", "true").lower() != "false"
INDEX_LIMIT = int(os.getenv("LEARNED_KNOWLEDGE_INDEX_LIMIT", "500"))
REQUEST_TIMEOUT = int(os.getenv("LEARNED_KNOWLEDGE_SYNC_TIMEOUT", "60"))

_sync_lock = threading.Lock()
_sync_running = False


def get_knowledge_service_url() -> str:
    """Return the configured Knowledge Service base URL."""
    return os.getenv("KNOWLEDGE_SERVICE_URL", "http://knowledge_service:5003").rstrip("/")


def trigger_learned_knowledge_sync(limit: int = INDEX_LIMIT) -> bool:
    """
    Start learned knowledge indexing in a background thread.

    Returns True when a new sync thread was started, False when disabled or an
    indexing job is already running in this process.
    """
    if not AUTO_SYNC_ENABLED:
        logger.info("Learned knowledge auto-sync is disabled.")
        return False

    global _sync_running  # pylint: disable=global-statement
    with _sync_lock:
        if _sync_running:
            logger.info("Learned knowledge sync already running; skipping duplicate trigger.")
            return False

        _sync_running = True

    thread = threading.Thread(
        target=_run_sync,
        args=(limit,),
        daemon=True,
    )
    thread.start()
    return True


def _run_sync(limit: int) -> None:
    """Call Knowledge Service indexing endpoint and release the process lock."""
    global _sync_running  # pylint: disable=global-statement

    try:
        url = f"{get_knowledge_service_url()}/knowledge/index/learned-components"
        logger.info("Starting learned knowledge sync: %s", url)

        response = requests.post(
            url,
            json={"limit": limit},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        logger.info("Learned knowledge sync completed: %s", response.json())

    except requests.exceptions.RequestException as error:
        logger.warning("Learned knowledge sync request failed: %s", error)
    except ValueError as error:
        logger.warning("Learned knowledge sync returned invalid JSON: %s", error)
    finally:
        with _sync_lock:
            _sync_running = False
