
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.evidence import Evidence
from app.models.investigation import Investigation
from app.schemas.evidence import EvidenceCreate, EvidenceRead

router = APIRouter(prefix="/evidence", tags=["evidence"])


@router.post("", response_model=EvidenceRead, status_code=201)
def create_evidence(
    payload: EvidenceCreate,
    db: Session = Depends(get_db),
) -> Evidence:
    """Create an evidence record, optionally linked to an investigation."""
    if payload.investigation_id is not None:
        investigation = db.scalar(
            select(Investigation).where(
                Investigation.id == payload.investigation_id
            )
        )
        if investigation is None:
            raise HTTPException(
                status_code=404,
                detail=f"Investigation {payload.investigation_id} not found",
            )

    evidence = Evidence(**payload.model_dump())
    db.add(evidence)
    db.commit()
    db.refresh(evidence)
    return evidence


@router.get("", response_model=list[EvidenceRead])
def list_evidence(
    investigation_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
) -> list[Evidence]:
    """List evidence, optionally filtered by investigation."""
    statement = select(Evidence).order_by(Evidence.id.desc())

    if investigation_id is not None:
        statement = statement.where(
            Evidence.investigation_id == investigation_id
        )

    statement = statement.offset(offset).limit(limit)
    return list(db.scalars(statement).all())


@router.get("/{evidence_id}", response_model=EvidenceRead)
def get_evidence(
    evidence_id: int,
    db: Session = Depends(get_db),
) -> Evidence:
    """Retrieve a single evidence record."""
    evidence = db.get(Evidence, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail=f"Evidence {evidence_id} not found",
        )

    return evidence
