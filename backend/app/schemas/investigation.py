
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.evidence import EvidenceRead


class InvestigationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    question: str = Field(min_length=1, max_length=2000)


class InvestigationStatusUpdate(BaseModel):
    status: Literal["in_progress", "completed", "failed"]


class InvestigationRead(BaseModel):
    id: int
    title: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    question: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigationDetail(InvestigationRead):
    evidence: list[EvidenceRead] = Field(default_factory=list)
