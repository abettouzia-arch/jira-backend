"""Shared schema definitions for generated reports."""

from typing import Any, Dict, Optional

from pydantic import Field

from shared.schemas.base_schema import BaseSchema


class ReportSummary(BaseSchema):
    """Minimal report metadata for listing endpoints."""

    report_id: str
    matrix_id: str
    analysis_id: str
    title: str
    generated_at: str
    summary: str


class ReportModel(BaseSchema):
    """Schema for a full persisted report."""

    report_id: str
    matrix_id: Optional[str] = None
    analysis_id: Optional[str] = None
    title: str
    generated_at: str
    summary: str
    migration_score: Optional[float] = None
    migration_recommendation: str = ""
    statistics: Dict[str, Any] = Field(default_factory=dict)
    sections: Dict[str, Any] = Field(default_factory=dict)
    raw_matrix: Dict[str, Any] = Field(default_factory=dict)
