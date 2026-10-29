
from typing import Any

from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.schemas.metric import MetricChange


def capture_release_comparison(
    db: Session,
    comparison: MetricChange,
    baseline_id: int,
    candidate_id: int,
) -> Evidence:
    """Persist the metrics and regression assessment for a release comparison."""
    assessment = comparison.regression_assessment

    evidence_data: dict[str, Any] = {
        "baseline": comparison.baseline.model_dump(mode="json"),
        "candidate": comparison.candidate.model_dump(mode="json"),
        "conversion_change_percentage_points": (
            comparison.conversion_change_percentage_points
        ),
        "error_rate_change_percentage_points": (
            comparison.error_rate_change_percentage_points
        ),
        "average_duration_change_ms": comparison.average_duration_change_ms,
        "interpretation": comparison.interpretation,
        "regression_assessment": (
            assessment.model_dump(mode="json")
            if assessment is not None
            else None
        ),
    }

    evidence = Evidence(
        evidence_type="regression_assessment",
        title=(
            f"Release comparison: "
            f"{comparison.baseline.release_version} → "
            f"{comparison.candidate.release_version}"
        ),
        description=(
            f"Comparison of baseline release ID {baseline_id} "
            f"with candidate release ID {candidate_id}. "
            "This record preserves the metrics and regression assessment "
            "returned by the comparison service."
        ),
        source="/api/v1/metrics/compare",
        data=evidence_data,
    )

    db.add(evidence)
    db.flush()
    return evidence
