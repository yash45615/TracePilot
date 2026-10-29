
from typing import Any

from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.investigation import Investigation
from app.schemas.metric import RegressionAssessment


def build_investigation_findings(
    db: Session,
    investigation: Investigation,
) -> dict[str, Any]:
    """Build deterministic findings from linked, structured evidence."""
    evidence_records = (
        db.query(Evidence)
        .filter(Evidence.investigation_id == investigation.id)
        .order_by(Evidence.created_at.desc(), Evidence.id.desc())
        .all()
    )

    assessments: list[RegressionAssessment] = []
    evidence_references: list[dict[str, Any]] = []
    limitations: list[str] = []
    malformed_count = 0

    for evidence in evidence_records:
        evidence_references.append(
            {
                "evidence_id": evidence.id,
                "title": evidence.title,
                "evidence_type": evidence.evidence_type,
                "source": evidence.source,
            }
        )

        if evidence.evidence_type != "regression_assessment":
            continue

        raw = evidence.data.get("regression_assessment")

        if not isinstance(raw, dict):
            malformed_count += 1
            limitations.append(
                f"Evidence {evidence.id} has no structured regression assessment."
            )
            continue

        try:
            assessment = RegressionAssessment.model_validate(raw)
        except (ValueError, TypeError):
            malformed_count += 1
            limitations.append(
                f"Evidence {evidence.id} contains an invalid regression assessment."
            )
            continue

        assessments.append(assessment)

    statuses = [assessment.status for assessment in assessments]
    has_positive = "regression_detected" in statuses
    has_negative = "no_regression_detected" in statuses
    has_inconclusive = "inconclusive" in statuses
    has_insufficient = "insufficient_data" in statuses

    if not evidence_records:
        conclusion = "insufficient_evidence"
        evidence_quality = "none"
        explanation = "No evidence is linked to this investigation."

    elif not assessments:
        conclusion = "insufficient_evidence"
        evidence_quality = "unusable"
        explanation = (
            "Linked evidence does not contain a valid structured "
            "regression assessment."
        )

    elif has_positive and has_negative:
        conclusion = "inconclusive"
        evidence_quality = "conflicting"
        explanation = (
            "Linked assessments disagree: at least one reports a regression "
            "signal and another reports no regression signal."
        )

    elif has_positive:
        conclusion = "regression_signal_detected"
        evidence_quality = (
            "partial"
            if has_inconclusive or has_insufficient or malformed_count
            else "structured"
        )
        explanation = (
            "At least one valid linked assessment reports a regression signal. "
            "Review other evidence and the limitations before drawing conclusions."
        )

    elif has_negative and not (has_inconclusive or has_insufficient):
        conclusion = "no_regression_signal_detected"
        evidence_quality = (
            "partial" if malformed_count else "structured"
        )
        explanation = (
            "All valid structured regression assessments report no regression "
            "signal. This does not prove that the release has no bugs."
        )

    else:
        conclusion = "inconclusive"
        evidence_quality = (
            "partial"
            if has_negative or malformed_count
            else "structured"
        )
        explanation = (
            "The available assessments include insufficient or inconclusive "
            "results, so the evidence does not support a clear conclusion."
        )

    if malformed_count:
        limitations.append(
            f"{malformed_count} regression assessment record(s) were unusable."
        )

    if has_insufficient:
        limitations.append(
            "At least one assessment reported insufficient data."
        )

    if has_inconclusive:
        limitations.append(
            "At least one assessment was statistically inconclusive."
        )

    limitations.append(
        "This engine evaluates stored assessments; it does not independently "
        "recalculate or verify their statistical results."
    )
    limitations.append(
        "A regression signal is not proof of causation or root cause."
    )

    return {
        "investigation_id": investigation.id,
        "investigation_title": investigation.title,
        "investigation_status": investigation.status,
        "question": investigation.question,
        "conclusion": conclusion,
        "evidence_quality": evidence_quality,
        "explanation": explanation,
        "evidence_count": len(evidence_records),
        "valid_assessment_count": len(assessments),
        "evidence_references": evidence_references,
        "limitations": list(dict.fromkeys(limitations)),
    }

