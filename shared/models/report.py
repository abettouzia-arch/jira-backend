"""Domain model for generated reports."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ReportModel:
    """Represents a saved migration report."""

    report_id: str
    matrix_id: Optional[str] = None
    analysis_id: Optional[str] = None
    generated_at: str = ""
    title: str = ""
    summary: str = ""
    migration_score: Optional[float] = None
    migration_recommendation: str = ""
    statistics: Dict[str, Any] = field(default_factory=dict)
    sections: Dict[str, Any] = field(default_factory=dict)
    raw_matrix: Dict[str, Any] = field(default_factory=dict)
    file_paths: Optional[List[str]] = field(default_factory=list)
