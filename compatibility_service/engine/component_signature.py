"""Stable signatures for caching compatibility analysis results."""

import hashlib
import json


def build_component_signature(component: dict) -> dict:
    """
    Build a deterministic signature for a parsed component.

    The cache key intentionally combines structural metadata, detected features,
    and a normalized source-code hash. This makes exact repeated scripts fast
    while avoiding unsafe reuse for unrelated components.
    """
    features = sorted(
        {
            str(feature).strip()
            for feature in component.get("features_detected", [])
            if str(feature).strip()
        }
    )
    source_code = _normalize_source(component.get("source_code", ""))
    source_hash = hashlib.sha256(source_code.encode("utf-8")).hexdigest()

    signature_payload = {
        "plugin": _normalize_text(component.get("plugin", "")),
        "component_type": _normalize_text(component.get("component_type", "")),
        "features": features,
        "source_hash": source_hash,
    }

    signature_key = hashlib.sha256(
        json.dumps(signature_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()

    return {
        "signature": signature_key,
        "plugin": signature_payload["plugin"],
        "component_type": signature_payload["component_type"],
        "features": features,
        "source_hash": source_hash,
    }


def _normalize_text(value: object) -> str:
    """Normalize short metadata fields for signature creation."""
    return str(value or "").strip().lower()


def _normalize_source(value: object) -> str:
    """Normalize source code enough to make line endings irrelevant."""
    text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.strip().splitlines())
