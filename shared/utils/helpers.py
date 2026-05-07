"""Shared helper utilities for common backend operations."""

from typing import Any, Dict

from bson import ObjectId


def serialize_document(value: Any) -> Any:
    """Convert MongoDB documents and ObjectIds into JSON-safe primitives."""
    if isinstance(value, ObjectId):
        return str(value)

    if isinstance(value, dict):
        return {key: serialize_document(item) for key, item in value.items() if key != "_id"}

    if isinstance(value, list):
        return [serialize_document(item) for item in value]

    return value


def hide_object_id(document: Dict[str, Any]) -> Dict[str, Any]:
    """Return a shallow copy of a document without the MongoDB `_id` field."""
    if not isinstance(document, dict):
        return document

    return {key: value for key, value in document.items() if key != "_id"}
