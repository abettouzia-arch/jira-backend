"""Domain model for parsed Jira export data."""

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class ParsedJiraData:
    """Container for parsed Jira source entities and components."""

    users: List[Dict[str, Any]] = field(default_factory=list)
    projects: List[Dict[str, Any]] = field(default_factory=list)
    issues: List[Dict[str, Any]] = field(default_factory=list)
    components: List[Dict[str, Any]] = field(default_factory=list)
