
from typing import Literal

from pydantic import BaseModel, Field


class EvidenceReference(BaseModel):
    evidence_id: int
    title: str
    evidence_type: str
    source: str


class InvestigationFindings(BaseModel):
    investigation_id: int
    investigation_title: str
    investigation_status: str
    question: str

    conclusion: Literal[
        "insufficient_evidence",
        "regression_signal_detected",
        "no_regression_signal_detected",
        "inconclusive",
    ]

    evidence_quality: Literal[
        "none",
        "unusable",
        "partial",
        "conflicting",
        "structured",
    ]

    explanation: str
    evidence_count: int
    valid_assessment_count: int
    evidence_references: list[EvidenceReference]
    limitations: list[str] = Field(default_factory=list)
