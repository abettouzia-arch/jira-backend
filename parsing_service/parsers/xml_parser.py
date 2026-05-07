"""XML parser for Jira export files used by the parsing service."""

import logging
import os
import sys
import uuid
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# pylint: disable=wrong-import-position
from parsing_service.ollama_client import OllamaConnectionError, generate_text
from parsing_service.utils.feature_detector import ai_detect_features, quick_scan_features
from shared.schemas.parsed_data_schema import (
    JiraComponent,
    JiraComponentCompatibility,
    JiraComponentLocation,
    JiraIssue,
    JiraProject,
    JiraUser,
    ParsedJiraData,
)

logger = logging.getLogger(__name__)


def clean_description_with_ai(raw_description: str) -> str:
    """
    Uses Ollama to process messy Jira descriptions into clean text.
    """
    if not raw_description or len(raw_description.strip()) == 0:
        return ""

    prompt = f"Clean this Jira description: {raw_description}"
    try:
        cleaned = generate_text(prompt=prompt, model="llama3")
        return cleaned.strip()
    except (OllamaConnectionError, RuntimeError, ValueError) as e:
        logger.warning("AI cleaning failed: %s", e)
        return raw_description


def parse_xml_streaming(file_path: str) -> ParsedJiraData:
    """
    Parses a giant Jira XML export file iteratively.
    """
    parsed_data = ParsedJiraData()
    logger.info("Starting streaming parse of %s", file_path)

    context = ET.iterparse(file_path, events=("end",))

    for _, elem in context:
        tag = elem.tag

        try:
            if tag == "User":
                user = JiraUser(
                    account_id=elem.attrib.get("id", elem.attrib.get("uuid", "")),
                    email_address=elem.attrib.get("emailAddress", ""),
                    display_name=elem.attrib.get("displayName", ""),
                    active=elem.attrib.get("active", "1") == "1",
                )
                parsed_data.users.append(user)
                elem.clear()

            elif tag == "Project":
                project = JiraProject(
                    id=elem.attrib.get("id", ""),
                    key=elem.attrib.get("key", ""),
                    name=elem.attrib.get("name", ""),
                    description=elem.attrib.get("description", ""),
                    project_type=elem.attrib.get("projectTypeKey", ""),
                )
                parsed_data.projects.append(project)
                elem.clear()

            elif tag == "Issue":
                raw_desc = elem.attrib.get("description", "")
                cleaned_ai_summary = None

                if raw_desc and len(raw_desc) > 500:
                    cleaned_ai_summary = clean_description_with_ai(raw_desc)

                issue = JiraIssue(
                    id=elem.attrib.get("id", ""),
                    key=elem.attrib.get("key", ""),
                    project_id=elem.attrib.get("project", ""),
                    summary=elem.attrib.get("summary", ""),
                    description=raw_desc,
                    issue_type=elem.attrib.get("type", ""),
                    status=elem.attrib.get("status", ""),
                    assignee=elem.attrib.get("assignee", ""),
                    reporter=elem.attrib.get("reporter", ""),
                    created=elem.attrib.get("created", ""),
                    updated=elem.attrib.get("updated", ""),
                    ai_summary=cleaned_ai_summary,
                )
                parsed_data.issues.append(issue)
                elem.clear()

            elif tag in ["WorkflowDescriptor", "Workflow", "GenericConfig"]:
                content = elem.text or ""

                for attr_val in elem.attrib.values():
                    if "import " in attr_val or "ComponentAccessor" in attr_val:
                        content += "\n" + attr_val

                if content:
                    quick_features = quick_scan_features(content)
                    ai_features = ai_detect_features(content, f"XML Node {tag}")
                    all_features = list(set(quick_features + ai_features))

                    if all_features:
                        comp_id = (
                        f"XML-{uuid.uuid5(uuid.NAMESPACE_URL, str(elem.attrib)).hex[:8].upper()}"
                        )
                        component_type = (
                            "workflow_script" if "Workflow" in tag else "config_script"
                        )

                        comp = JiraComponent(
                            component_id=comp_id,
                            component_type=component_type,
                            plugin="native",
                            location=JiraComponentLocation(
                                workflow=elem.attrib.get("name", ""),
                                file_path="entities.xml",
                            ),
                            features_detected=all_features,
                            source_code=content,
                            compatibility=JiraComponentCompatibility(
                                cloud_status="",
                                risk_level="",
                            ),
                            recommended_action="",
                            report_text="",
                        )
                        parsed_data.components.append(comp)

                elem.clear()

        except (ET.ParseError, ValueError, TypeError, AttributeError) as e:
            logger.error("Error parsing element %s: %s", tag, e)
            elem.clear()

    logger.info(
        "Parsing complete: %s Projects, %s Issues, %s Components.",
        len(parsed_data.projects),
        len(parsed_data.issues),
        len(parsed_data.components),
    )
    return parsed_data
