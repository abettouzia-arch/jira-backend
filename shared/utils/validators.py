"""Shared validation helpers for service payloads."""

import uuid
from typing import Iterable, List


def is_valid_uuid(value: str) -> bool:
    """Check whether a string is a valid UUID."""
    try:
        uuid.UUID(value)
        return True
    except (ValueError, TypeError):
        return False


def require_fields(payload: dict, required_fields: Iterable[str]) -> List[str]:
    """Return a list of missing required fields from a payload."""
    return [field for field in required_fields if field not in payload or payload[field] is None]
