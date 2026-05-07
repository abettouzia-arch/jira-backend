"""
JSON export utilities for Report Service.

Provides clean JSON serialization for generated migration reports.
"""

import json
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = BASE_DIR / "generated_reports"


def export_report_to_json(
    report: dict,
    output_dir: str | Path = DEFAULT_OUTPUT_DIR,
) -> str:
    """Export a report dict to a JSON file."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    report_id = report.get("report_id", "unknown-report")
    file_path = output_path / f"{report_id}.json"

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(
            _make_json_safe(report),
            file,
            indent=2,
            ensure_ascii=False,
        )

    return str(file_path)


def report_to_json_string(report: dict) -> str:
    """Convert a report dict to a pretty JSON string."""
    return json.dumps(
        _make_json_safe(report),
        indent=2,
        ensure_ascii=False,
    )


def _make_json_safe(value):
    """Recursively convert non-JSON-safe values into serializable values."""
    if isinstance(value, dict):
        return {
            str(key): _make_json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [_make_json_safe(item) for item in value]

    if isinstance(value, datetime):
        return value.isoformat()

    if hasattr(value, "__str__") and not isinstance(
        value,
        (str, int, float, bool, type(None)),
    ):
        return str(value)

    return value
