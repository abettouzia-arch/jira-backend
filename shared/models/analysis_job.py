"""Domain model for analysis jobs."""

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class AnalysisJob:
    """Represents a job record stored in MongoDB."""

    job_id: str
    job_type: str = "FULL_ANALYSIS"
    status: str = "QUEUED"
    payload: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Dict[str, Any] = field(default_factory=dict)
