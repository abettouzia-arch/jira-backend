"""Shared Pydantic schema base class."""

from pydantic import BaseModel


class BaseSchema(BaseModel):
    """Base schema with common configuration for service models."""

    class Config:
        """Pydantic configuration for base schema."""
        extra = "ignore"
        orm_mode = True
        allow_population_by_field_name = True
