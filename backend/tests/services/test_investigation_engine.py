
from fastapi.testclient import TestClient


def create_investigation(client: TestClient) -> int:
    response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Regression investigation",
            "question": "Did the latest release increase errors?",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def add_evidence(
    client: TestClient,
    investigation_id: int,
    *,
    evidence_type: str,
    data: dict,
    title: str = "Test evidence",
) -> None:
    response = client.post(
        "/api/v1/evidence",
        json={
            "investigation_id": investigation_id,
            "evidence_type": evidence_type,
            "title": title,
            "description": "Evidence for investigation engine testing.",
            "source": "automated_test",
            "data": data,
        },
    )
    assert response.status_code == 201


def get_findings(client: TestClient, investigation_id: int) -> dict:
    response = client.get(
        f"/api/v1/investigations/{investigation_id}/findings"
    )
    assert response.status_code == 200
    return response.json()


def test_findings_report_insufficient_evidence(
    client: TestClient,
) -> None:
    investigation_id = create_investigation(client)

    findings = get_findings(client, investigation_id)

    assert findings["conclusion"] == "insufficient_evidence"
    assert findings["evidence_count"] == 0
    assert findings["evidence_references"] == []
    assert findings["limitations"]


def test_findings_detect_regression_signal(
    client: TestClient,
) -> None:
    investigation_id = create_investigation(client)
    add_evidence(
        client,
        investigation_id,
        evidence_type="regression_assessment",
        title="Regression assessment",
        data={
            "regression_assessment": {
                "status": "regression_detected",
                "reason": "Candidate error rate increased significantly.",
                "baseline_error_rate": 0.01,
                "candidate_error_rate": 0.08,
                "change_percentage_points": 7.0,
                "baseline_ci_95": [0.0, 0.03],
                "candidate_ci_95": [0.04, 0.12],
                "p_value": 0.001,
                "alpha": 0.05,
                "minimum_increase_percentage_points": 1.0,
            }
        },
    )

    findings = get_findings(client, investigation_id)

    assert findings["conclusion"] == "regression_signal_detected"
    assert findings["evidence_count"] == 1
    assert "root cause" in findings["limitations"][-1].lower()


def test_findings_report_no_regression_signal(
    client: TestClient,
) -> None:
    investigation_id = create_investigation(client)
    add_evidence(
        client,
        investigation_id,
        evidence_type="regression_assessment",
        data={
            "regression_assessment": {
                "status": "no_regression_detected",
                "reason": "No statistically significant increase detected.",
                "baseline_error_rate": 0.02,
                "candidate_error_rate": 0.021,
                "change_percentage_points": 0.1,
                "baseline_ci_95": [0.01, 0.03],
                "candidate_ci_95": [0.01, 0.04],
                "p_value": 0.8,
                "alpha": 0.05,
                "minimum_increase_percentage_points": 1.0,
            }
        },
    )

    findings = get_findings(client, investigation_id)

    assert findings["conclusion"] == "no_regression_signal_detected"


def test_findings_report_inconclusive_assessment(
    client: TestClient,
) -> None:
    investigation_id = create_investigation(client)
    add_evidence(
        client,
        investigation_id,
        evidence_type="regression_assessment",
        data={
            "regression_assessment": {
                "status": "inconclusive",
                "reason": "The evidence is inconclusive.",
                "baseline_error_rate": None,
                "candidate_error_rate": None,
                "change_percentage_points": None,
                "baseline_ci_95": None,
                "candidate_ci_95": None,
                "p_value": None,
                "alpha": 0.05,
                "minimum_increase_percentage_points": 1.0,
            }
        },
    )

    findings = get_findings(client, investigation_id)

    assert findings["conclusion"] == "inconclusive"


def test_findings_ignore_unstructured_evidence_for_regression(
    client: TestClient,
) -> None:
    investigation_id = create_investigation(client)
    add_evidence(
        client,
        investigation_id,
        evidence_type="event_sample",
        data={"event_name": "checkout_failed"},
    )

    findings = get_findings(client, investigation_id)

    assert findings["conclusion"] == "insufficient_evidence"
    assert findings["evidence_count"] == 1
    assert findings["evidence_references"][0]["evidence_type"] == "event_sample"


def test_findings_for_missing_investigation_return_404(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/investigations/999999/findings")

    assert response.status_code == 404



def test_conflicting_assessments_produce_inconclusive_findings(client):
    investigation_response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Conflicting evidence",
            "question": "Did the new release increase the error rate?",
        },
    )
    assert investigation_response.status_code == 201
    investigation_id = investigation_response.json()["id"]

    positive_assessment = {
        "status": "regression_detected",
        "reason": "The increase is statistically significant.",
        "baseline_error_rate": 1.0,
        "candidate_error_rate": 5.0,
        "change_percentage_points": 4.0,
        "baseline_ci_95": [0.5, 1.5],
        "candidate_ci_95": [3.0, 7.0],
        "p_value": 0.01,
        "alpha": 0.05,
        "minimum_increase_percentage_points": 1.0,
    }
    negative_assessment = {
        **positive_assessment,
        "status": "no_regression_detected",
        "reason": "The increase is below the configured threshold.",
    }

    for assessment in (positive_assessment, negative_assessment):
        response = client.post(
            "/api/v1/evidence",
            json={
                "investigation_id": investigation_id,
                "evidence_type": "regression_assessment",
                "title": "Regression assessment",
                "description": "Test assessment",
                "source": "automated_test",
                "data": {"regression_assessment": assessment},
            },
        )
        assert response.status_code in (200, 201)

    findings_response = client.get(
        f"/api/v1/investigations/{investigation_id}/findings"
    )
    assert findings_response.status_code == 200

    findings = findings_response.json()
    assert findings["conclusion"] == "inconclusive"
    assert findings["evidence_quality"] == "conflicting"
    assert findings["valid_assessment_count"] == 2
    assert findings["evidence_count"] == 2
