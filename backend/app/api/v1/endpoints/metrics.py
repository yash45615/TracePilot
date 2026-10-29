
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.event import ProductEvent
from app.models.release import Release
from app.schemas.metric import (
    MetricChange,
    RegressionAssessment,
    ReleaseMetrics,
)
from app.services.evidence_capture import capture_release_comparison
from app.services.regression_detection import detect_error_rate_regression
from app.services.release_comparison import (
    calculate_release_metrics,
    compare_releases,
)

router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_error_counts(db: Session, release_id: int) -> tuple[int, int]:
    """Return the number of error events and total events for a release."""
    total_events = (
        db.scalar(
            select(func.count(ProductEvent.id)).where(
                ProductEvent.release_id == release_id
            )
        )
        or 0
    )

    error_events = (
        db.scalar(
            select(func.count(ProductEvent.id)).where(
                ProductEvent.release_id == release_id,
                ProductEvent.is_error.is_(True),
            )
        )
        or 0
    )

    return error_events, total_events


@router.get("/release", response_model=ReleaseMetrics)
def get_release_metrics(
    release_id: int = Query(gt=0),
    db: Session = Depends(get_db),
) -> ReleaseMetrics:
    """Calculate product and reliability metrics for a single release."""
    release = db.scalar(select(Release).where(Release.id == release_id))

    if release is None:
        raise HTTPException(
            status_code=404,
            detail=f"Release {release_id} not found",
        )

    return calculate_release_metrics(db, release)


@router.get("/compare", response_model=MetricChange)
def get_release_comparison(
    baseline_id: int = Query(gt=0),
    candidate_id: int = Query(gt=0),
    db: Session = Depends(get_db),
) -> MetricChange:
    """Compare two releases and persist the regression evidence."""
    if baseline_id == candidate_id:
        raise HTTPException(
            status_code=422,
            detail="Baseline and candidate releases must be different",
        )

    baseline = db.scalar(select(Release).where(Release.id == baseline_id))
    if baseline is None:
        raise HTTPException(
            status_code=404,
            detail=f"Baseline release {baseline_id} not found",
        )

    candidate = db.scalar(select(Release).where(Release.id == candidate_id))
    if candidate is None:
        raise HTTPException(
            status_code=404,
            detail=f"Candidate release {candidate_id} not found",
        )

    comparison = compare_releases(db, baseline, candidate)

    baseline_errors, baseline_total = get_error_counts(db, baseline_id)
    candidate_errors, candidate_total = get_error_counts(db, candidate_id)

    assessment_data = detect_error_rate_regression(
        baseline_errors=baseline_errors,
        baseline_total=baseline_total,
        candidate_errors=candidate_errors,
        candidate_total=candidate_total,
    )

    assessment = RegressionAssessment.model_validate(assessment_data)

    comparison = comparison.model_copy(
        update={"regression_assessment": assessment}
    )

    capture_release_comparison(
        db=db,
        comparison=comparison,
        baseline_id=baseline_id,
        candidate_id=candidate_id,
    )
    db.commit()

    return comparison
