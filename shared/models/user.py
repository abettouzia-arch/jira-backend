"""Domain model for Jira users."""

from dataclasses import dataclass


@dataclass
class JiraUser:
    """Represents a Jira user extracted from the source instance."""

    account_id: str
    email_address: str = ""
    display_name: str = ""
    active: bool = True
