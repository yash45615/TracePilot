from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.event import ProductEvent
from app.models.release import Release
from app.schemas.metric import MetricChange, ReleaseMetrics


def calculate_release_metrics(db: Session, release: Release) -> ReleaseMetrics:
    events = list(
        db.scalars(select(ProductEvent).where(ProductEvent.release_id == release.id)).all()
    )

    total_events = len(events)
    unique_users = len({event.user_id for event in events})

    conversion_users = {event.user_id for event in events if event.event_name == "conversion"}
    error_events = sum(1 for event in events if event.is_error)
    durations = [event.duration_ms for event in events if event.duration_ms is not None]

    conversion_rate = len(conversion_users) / unique_users * 100 if unique_users else 0.0
    error_rate = error_events / total_events * 100 if total_events else 0.0
    average_duration = sum(durations) / len(durations) if durations else None

    return ReleaseMetrics(
        release_id=release.id,
        release_version=release.version,
        total_events=total_events,
        unique_users=unique_users,
        conversion_rate=round(conversion_rate, 2),
        error_rate=round(error_rate, 2),
        average_duration_ms=(round(average_duration, 2) if average_duration is not None else None),
    )


def compare_releases(db: Session, baseline: Release, candidate: Release) -> MetricChange:
    baseline_metrics = calculate_release_metrics(db, baseline)
    candidate_metrics = calculate_release_metrics(db, candidate)

    conversion_change = round(
        candidate_metrics.conversion_rate - baseline_metrics.conversion_rate, 2
    )
    error_change = round(candidate_metrics.error_rate - baseline_metrics.error_rate, 2)

    duration_change = None
    if (
        baseline_metrics.average_duration_ms is not None
        and candidate_metrics.average_duration_ms is not None
    ):
        duration_change = round(
            candidate_metrics.average_duration_ms - baseline_metrics.average_duration_ms,
            2,
        )

    interpretation = []

    if conversion_change < 0:
        interpretation.append(
            f"Conversion rate decreased by {abs(conversion_change):.2f} percentage points."
        )
    elif conversion_change > 0:
        interpretation.append(
            f"Conversion rate increased by {conversion_change:.2f} percentage points."
        )

    if error_change > 0:
        interpretation.append(f"Error rate increased by {error_change:.2f} percentage points.")
    elif error_change < 0:
        interpretation.append(f"Error rate decreased by {abs(error_change):.2f} percentage points.")

    if duration_change is not None and duration_change > 0:
        interpretation.append(f"Average event duration increased by {duration_change:.2f} ms.")
    elif duration_change is not None and duration_change < 0:
        interpretation.append(f"Average event duration decreased by {abs(duration_change):.2f} ms.")

    if not interpretation:
        interpretation.append("No change was detected in the measured metrics.")

    return MetricChange(
        baseline=baseline_metrics,
        candidate=candidate_metrics,
        conversion_change_percentage_points=conversion_change,
        error_rate_change_percentage_points=error_change,
        average_duration_change_ms=duration_change,
        interpretation=interpretation,
    )
