from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class EvidenceCreate(BaseModel):
    investigation_id: int | None = Field(default=None, gt=0)
    evidence_type: Literal[
        "release_metrics",
        "regression_assessment",
        "event_sample",
    ]
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=2000)
    source: str = Field(min_length=1, max_length=200)
    data: dict[str, Any] = Field(default_factory=dict)


class EvidenceRead(BaseModel):
    id: int
    investigation_id: int | None
    evidence_type: str
    title: str
    description: str
    source: str
    data: dict[str, Any]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
