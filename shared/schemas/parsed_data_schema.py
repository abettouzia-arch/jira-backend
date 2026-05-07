"""Pydantic schemas for parsed Jira entities and migration components."""

from typing import List, Optional

from pydantic import BaseModel, Field


class JiraUser(BaseModel):
    """Represents a Jira user extracted from the source instance."""

    account_id: str
    email_address: str = ""
    display_name: str = ""
    active: bool = True


class JiraProject(BaseModel):
    """Represents a Jira project extracted from the source instance."""

    id: str
    key: str
    name: str
    description: Optional[str] = None
    project_type: Optional[str] = None


class JiraIssue(BaseModel):
    """Represents a Jira issue extracted from the source instance."""

    id: str
    key: str
    project_id: str
    summary: str
    description: Optional[str] = None
    issue_type: str
    status: str
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    created: str
    updated: str
    ai_summary: Optional[str] = None


class JiraComponentLocation(BaseModel):
    """Stores the logical location of a detected Jira component."""

    workflow: Optional[str] = ""
    transition: Optional[str] = ""
    file_path: Optional[str] = ""


class JiraComponentCompatibility(BaseModel):
    """Stores compatibility assessment fields for a Jira component."""

    cloud_status: Optional[str] = ""
    risk_level: Optional[str] = ""


class JiraComponent(BaseModel):
    """Represents a detected migration-relevant Jira component."""

    component_id: str
    component_type: str
    plugin: str
    location: JiraComponentLocation = Field(default_factory=JiraComponentLocation)
    features_detected: List[str] = Field(default_factory=list)
    source_code: Optional[str] = ""
    compatibility: Optional[JiraComponentCompatibility] = Field(
        default_factory=JiraComponentCompatibility
    )
    recommended_action: Optional[str] = ""
    report_text: Optional[str] = ""


class ParsedJiraData(BaseModel):
    """Container for all entities and components extracted during parsing."""

    users: List[JiraUser] = Field(default_factory=list)
    projects: List[JiraProject] = Field(default_factory=list)
    issues: List[JiraIssue] = Field(default_factory=list)
    components: List[JiraComponent] = Field(default_factory=list)
