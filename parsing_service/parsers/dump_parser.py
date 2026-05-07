"""
Dump Parser for Jira Migration parsing service.

Handles .json and .sql files found in the Jira export.
Scans for embedded scripts, configuration blocks, and custom field logic
to detect features using Ollama AI.
"""

import json
import logging
import os
import re
import sys
import uuid
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# pylint: disable=wrong-import-position
from parsing_service.utils.feature_detector import ai_detect_features, quick_scan_features
from shared.schemas.parsed_data_schema import (
    JiraComponent,
    JiraComponentCompatibility,
    JiraComponentLocation,
)

logger = logging.getLogger(__name__)


def parse_json_dump(file_info: dict) -> list[JiraComponent]:
    """
    Parses a JSON dump and looks for script nodes or config blocks.
    """
    file_path = file_info["full_path"]
    filename = file_info["filename"]
    components = []

    try:
        with open(file_path, "r", encoding="utf-8-sig") as file:
            data = json.load(file)

        def find_scripts(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    find_scripts(value, f"{path}.{key}" if path else key)
            elif isinstance(obj, list):
                for index, value in enumerate(obj):
                    find_scripts(value, f"{path}[{index}]")
            elif isinstance(obj, str):
                if "import " in obj or ("{" in obj and "}" in obj):
                    comp = create_component_from_snip(
                        obj,
                        f"{filename} at {path}",
                        filename,
                    )
                    if comp:
                        components.append(comp)

        find_scripts(data)

    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError) as e:
        logger.error("Failed to parse JSON dump %s: %s", filename, e)

    return components


def parse_sql_dump(file_info: dict) -> list[JiraComponent]:
    """
    Parses a SQL dump by scanning for INSERT statements into configuration tables.
    """
    file_path = file_info["full_path"]
    filename = file_info["filename"]
    components = []

    script_pattern = re.compile(
        r"INSERT INTO .*?VALUES.*?(['\"])(.*?)\1",
        re.IGNORECASE | re.DOTALL,
    )

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            for line in file:
                if "INSERT" in line:
                    matches = script_pattern.findall(line)
                    for match in matches:
                        content = match[1]
                        if "import " in content or "ComponentAccessor" in content:
                            comp = create_component_from_snip(
                                content,
                                f"{filename} SQL Insert",
                                filename,
                            )
                            if comp:
                                components.append(comp)

    except (OSError, UnicodeDecodeError, TypeError, ValueError, re.error) as e:
        logger.error("Failed to parse SQL dump %s: %s", filename, e)

    return components


def create_component_from_snip(
    content: str,
    display_location: str,
    filename: str,
) -> JiraComponent | None:
    """
    Helper to turn a snippet of code/config into a JiraComponent.
    """
    if len(content.strip()) < 10:
        return None

    quick_features = quick_scan_features(content)
    ai_features = ai_detect_features(content, display_location)
    all_features = list(set(quick_features + ai_features))

    if not all_features:
        return None

    component_id = f"DMP-{uuid.uuid5(uuid.NAMESPACE_URL, display_location).hex[:8].upper()}"

    return JiraComponent(
        component_id=component_id,
        component_type="script",
        plugin="unknown",
        location=JiraComponentLocation(file_path=filename),
        features_detected=all_features,
        source_code=content,
        compatibility=JiraComponentCompatibility(cloud_status="", risk_level=""),
        recommended_action="",
        report_text="",
    )


def parse_dump_files(file_list: list[dict]) -> list[JiraComponent]:
    """
    Main entry point for dump files.
    """
    all_components = []
    for file_info in file_list:
        ext = Path(file_info["filename"]).suffix.lower()
        if ext == ".json":
            all_components.extend(parse_json_dump(file_info))
        elif ext in [".sql", ".dump"]:
            all_components.extend(parse_sql_dump(file_info))

    return all_components
