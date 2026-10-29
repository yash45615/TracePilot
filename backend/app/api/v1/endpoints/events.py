from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import ProductEvent
from app.schemas.event import EventCreate, EventRead
from app.services.event_ingestion import ingest_event

router = APIRouter(prefix="/events", tags=["Events"])


@router.post("", response_model=EventRead, status_code=status.HTTP_201_CREATED)
def create_event(
    payload: EventCreate,
    db: Session = Depends(get_db),
) -> ProductEvent:
    try:
        return ingest_event(db, payload)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("", response_model=list[EventRead])
def list_events(
    release_id: int | None = Query(default=None, gt=0),
    limit: int = Query(default=100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[ProductEvent]:
    statement = select(ProductEvent).order_by(ProductEvent.id.desc())

    if release_id is not None:
        statement = statement.where(ProductEvent.release_id == release_id)

    return list(db.scalars(statement.limit(limit)).all())
