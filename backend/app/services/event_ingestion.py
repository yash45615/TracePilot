from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import ProductEvent
from app.models.release import Release
from app.schemas.event import EventCreate


def ingest_event(db: Session, payload: EventCreate) -> ProductEvent:
    release = db.scalar(select(Release).where(Release.id == payload.release_id))
    if release is None:
        raise ValueError(f"Release {payload.release_id} does not exist")

    event_data = payload.model_dump(exclude={"occurred_at"})
    occurred_at = payload.occurred_at

    event = ProductEvent(
        **event_data,
        **({"occurred_at": occurred_at} if occurred_at else {}),
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event
