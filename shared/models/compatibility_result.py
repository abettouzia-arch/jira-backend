"""Domain model for compatibility assessment results."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class CompatibilityResult:
    """Represents the compatibility outcomes for a Jira component."""

    matrix_id: str
    analysis_id: str
    analyzed_at: str
    components: List[Dict[str, Any]] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    overall_risk: str = ""
    migration_score: Optional[float] = None
