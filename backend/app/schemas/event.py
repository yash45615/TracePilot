from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EventCreate(BaseModel):
    event_name: str = Field(min_length=1, max_length=150)
    user_id: str = Field(min_length=1, max_length=150)
    release_id: int = Field(gt=0)
    occurred_at: datetime | None = None
    duration_ms: float | None = Field(default=None, ge=0)
    is_error: bool = False
    properties: dict[str, Any] = Field(default_factory=dict)

    @field_validator("occurred_at")
    @classmethod
    def require_aware_datetime(cls, value: datetime | None) -> datetime | None:
        if value is not None and value.tzinfo is None:
            raise ValueError("occurred_at must include a timezone")
        return value


class EventRead(BaseModel):
    id: int
    event_name: str
    user_id: str
    release_id: int
    occurred_at: datetime
    duration_ms: float | None
    is_error: bool
    properties: dict[str, Any]

    model_config = ConfigDict(from_attributes=True)
