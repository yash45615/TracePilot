
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.evidence import EvidenceRead


class InvestigationSummary(BaseModel):
    investigation_id: int
    title: str
    question: str
    status: str
    created_at: datetime
    evidence_count: int
    evidence: list[EvidenceRead]
    summary: str
    limitations: list[str]

    model_config = ConfigDict(from_attributes=True)
