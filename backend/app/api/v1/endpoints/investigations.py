
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.evidence import Evidence
from app.models.investigation import Investigation
from app.schemas.investigation import (
    InvestigationCreate,
    InvestigationDetail,
    InvestigationRead,
    InvestigationStatusUpdate,
)
from app.schemas.investigation_findings import InvestigationFindings
from app.schemas.investigation_summary import InvestigationSummary
from app.services.investigation_engine import build_investigation_findings

router = APIRouter(prefix="/investigations", tags=["investigations"])


@router.post("", response_model=InvestigationRead, status_code=201)
def create_investigation(
    payload: InvestigationCreate,
    db: Session = Depends(get_db),
) -> Investigation:
    """Create a new investigation."""
    investigation = Investigation(
        title=payload.title,
        question=payload.question,
    )
    db.add(investigation)
    db.commit()
    db.refresh(investigation)
    return investigation


@router.get("", response_model=list[InvestigationRead])
def list_investigations(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Investigation]:
    """List investigations, newest first."""
    statement = (
        select(Investigation)
        .order_by(Investigation.id.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.get("/{investigation_id}", response_model=InvestigationDetail)
def get_investigation(
    investigation_id: int,
    db: Session = Depends(get_db),
) -> InvestigationDetail:
    """Retrieve an investigation and its associated evidence."""
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation {investigation_id} not found",
        )

    evidence = list(
        db.scalars(
            select(Evidence)
            .where(Evidence.investigation_id == investigation_id)
            .order_by(Evidence.id.desc())
        ).all()
    )

    return InvestigationDetail(
        id=investigation.id,
        title=investigation.title,
        question=investigation.question,
        status=investigation.status,
        created_at=investigation.created_at,
        evidence=evidence,
    )


@router.patch("/{investigation_id}/status", response_model=InvestigationRead)
def update_investigation_status(
    investigation_id: int,
    payload: InvestigationStatusUpdate,
    db: Session = Depends(get_db),
) -> InvestigationRead:
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation {investigation_id} not found",
        )

    allowed_transitions = {
        "pending": {"in_progress", "failed"},
        "in_progress": {"completed", "failed"},
        "completed": set(),
        "failed": set(),
    }

    if payload.status not in allowed_transitions.get(
        investigation.status, set()
    ):
        raise HTTPException(
            status_code=409,
            detail=(
                f"Cannot change investigation status from "
                f"'{investigation.status}' to '{payload.status}'"
            ),
        )

    investigation.status = payload.status
    db.commit()
    db.refresh(investigation)

    return investigation


@router.get(
    "/{investigation_id}/summary",
    response_model=InvestigationSummary,
)
def get_investigation_summary(
    investigation_id: int,
    db: Session = Depends(get_db),
) -> InvestigationSummary:
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation {investigation_id} not found",
        )

    evidence_records = list(
        db.scalars(
            select(Evidence)
            .where(Evidence.investigation_id == investigation_id)
            .order_by(Evidence.created_at.desc(), Evidence.id.desc())
        ).all()
    )

    if evidence_records:
        summary = (
            f"Investigation '{investigation.title}' has "
            f"{len(evidence_records)} linked evidence record(s). "
            "Review the records below to assess the question. "
            "No independent root-cause conclusion has been generated."
        )
        limitations = [
            "This summary describes stored evidence only.",
            "Linked evidence has not been independently verified.",
            "A root cause has not been established by this endpoint.",
        ]
    else:
        summary = (
            f"Investigation '{investigation.title}' has no linked evidence "
            "records yet. There is not enough recorded evidence to assess "
            "the investigation question."
        )
        limitations = [
            "No evidence is linked to this investigation.",
            "The root cause is unknown.",
        ]

    return InvestigationSummary(
        investigation_id=investigation.id,
        title=investigation.title,
        question=investigation.question,
        status=investigation.status,
        created_at=investigation.created_at,
        evidence_count=len(evidence_records),
        evidence=evidence_records,
        summary=summary,
        limitations=limitations,
    )


@router.get(
    "/{investigation_id}/findings",
    response_model=InvestigationFindings,
)
def get_investigation_findings(
    investigation_id: int,
    db: Session = Depends(get_db),
) -> InvestigationFindings:
    investigation = db.get(Investigation, investigation_id)

    if investigation is None:
        raise HTTPException(
            status_code=404,
            detail=f"Investigation {investigation_id} not found",
        )

    findings = build_investigation_findings(db, investigation)
    return InvestigationFindings.model_validate(findings)
