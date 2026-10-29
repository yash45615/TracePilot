from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.release import Release
from app.schemas.release import ReleaseCreate, ReleaseRead

router = APIRouter(prefix="/releases", tags=["Releases"])


@router.post("", response_model=ReleaseRead, status_code=status.HTTP_201_CREATED)
def create_release(
    payload: ReleaseCreate,
    db: Session = Depends(get_db),
) -> Release:
    release = Release(version=payload.version.strip(), name=payload.name.strip())

    if not release.version or not release.name:
        raise HTTPException(status_code=422, detail="Version and name cannot be blank")

    db.add(release)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="A release with this version already exists",
        ) from None

    db.refresh(release)
    return release


@router.get("", response_model=list[ReleaseRead])
def list_releases(db: Session = Depends(get_db)) -> list[Release]:
    return list(db.scalars(select(Release).order_by(Release.created_at.desc())).all())
