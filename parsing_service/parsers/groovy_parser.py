"""
Groovy Parser for Jira Migration parsing service.

Reads .groovy scripts exported from Jira (ScriptRunner, JSU, etc.),
uses AI to detect which dangerous Java API features are used,
and returns structured JiraComponent objects ready for the Compatibility Service.
"""

import logging
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# pylint: disable=wrong-import-position
from parsing_service.utils.feature_detector import ai_detect_features, quick_scan_features
from shared.schemas.parsed_data_schema import (
    JiraComponent,
    JiraComponentCompatibility,
    JiraComponentLocation,
)

logger = logging.getLogger(__name__)


def read_text_file(file_path: str) -> str:
    """
    Read a text file using common encodings.

    This prevents malformed source_code when files are created with UTF-16
    or Windows-specific encodings.
    """
    encodings = [
        "utf-8-sig",
        "utf-8",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "cp1252",
        "latin-1",
    ]

    for encoding in encodings:
        try:
            with open(file_path, "r", encoding=encoding) as file:
                content = file.read()

            if "\x00" not in content:
                return content

        except (UnicodeDecodeError, OSError):
            continue

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as file:
            return file.read().replace("\x00", "")
    except OSError as error:
        logger.error("Cannot read file %s: %s", file_path, error)
        return ""


def detect_component_type(code: str, filename: str) -> str:
    """
    Heuristic detection of the component type based on filename or code content.
    """
    name_lower = filename.lower()
    code_lower = code.lower()

    if "validator" in name_lower or "validator" in code_lower:
        return "workflow_validator"
    if "postfunction" in name_lower or "post_function" in name_lower or "postFunction" in code:
        return "post_function"
    if "listener" in name_lower or "AbstractIssueEventListener" in code:
        return "listener"
    if "condition" in name_lower or "condition" in code_lower:
        return "workflow_condition"
    if "rest" in name_lower or "@Path" in code:
        return "api_usage"
    return "script"


def detect_plugin(code: str) -> str:
    """Classify which Jira plugin the script originates from."""
    if "com.onresolve" in code or "com.adaptavist" in code:
        return "ScriptRunner"
    if "com.jsum" in code or "jsu" in code.lower():
        return "JSU"
    if "com.atlassian" in code:
        return "native"
    return "MISC"


def parse_groovy_file(file_info: dict) -> JiraComponent:
    """
    Parse a single .groovy file and return a JiraComponent.
    """
    file_path = file_info["full_path"]
    filename = file_info["filename"]

    logger.info("Parsing Groovy file: %s (%s KB)", filename, file_info["size_kb"])

    code = read_text_file(file_path)

    quick_features = quick_scan_features(code)
    ai_features = ai_detect_features(code, filename)
    all_features = list(set(quick_features + ai_features))

    component_type = detect_component_type(code, filename)
    plugin = detect_plugin(code)

    component_id = f"GRV-{uuid.uuid5(uuid.NAMESPACE_URL, filename).hex[:8].upper()}"

    component = JiraComponent(
        component_id=component_id,
        component_type=component_type,
        plugin=plugin,
        location=JiraComponentLocation(
            workflow="",
            transition="",
            file_path=filename,
        ),
        features_detected=all_features,
        source_code=code,
        compatibility=JiraComponentCompatibility(cloud_status="", risk_level=""),
        recommended_action="",
        report_text="",
    )

    return component


def parse_groovy_files(file_list: list[dict]) -> list[JiraComponent]:
    """
    Main entry point: parse all .groovy files routed by zip_handler.
    """
    components = []

    for file_info in file_list:
        try:
            component = parse_groovy_file(file_info)
            components.append(component)
        except (KeyError, TypeError, ValueError, OSError) as error:
            logger.error(
                "Failed to parse Groovy file %s: %s",
                file_info.get("filename", "<unknown>"),
                error,
            )

    return components
