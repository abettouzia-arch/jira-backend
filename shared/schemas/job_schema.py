"""Shared schema definitions for worker jobs."""

from typing import Any, Dict, Optional

from pydantic import Field

from shared.schemas.base_schema import BaseSchema


class JobPayload(BaseSchema):
    """Schema for optional job payload data."""

    payload: Dict[str, Any] = Field(default_factory=dict)


class JobModel(BaseSchema):
    """Schema representing a persisted job record."""

    job_id: str
    job_type: str
    status: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    error: Optional[str] = None
    result: Dict[str, Any] = Field(default_factory=dict)
