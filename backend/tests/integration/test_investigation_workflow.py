
from fastapi.testclient import TestClient


def create_release(
    client: TestClient,
    version: str,
    name: str,
) -> int:
    response = client.post(
        "/api/v1/releases",
        json={"version": version, "name": name},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def add_events(
    client: TestClient,
    release_id: int,
    total: int,
    error_count: int,
) -> None:
    for index in range(total):
        response = client.post(
            "/api/v1/events",
            json={
                "event_name": "checkout",
                "user_id": f"workflow-{release_id}-{index}",
                "release_id": release_id,
                "is_error": index < error_count,
                "duration_ms": 100 if index >= error_count else 500,
                "properties": {},
            },
        )
        assert response.status_code in (200, 201), response.text


def test_release_regression_investigation_workflow(
    client: TestClient,
) -> None:
    # 1. Create the baseline and candidate releases.
    baseline_id = create_release(client, "10.0.0", "Baseline")
    candidate_id = create_release(client, "10.1.0", "Candidate")

    # 2. Generate a clear regression signal.
    add_events(client, baseline_id, total=100, error_count=1)
    add_events(client, candidate_id, total=100, error_count=25)

    # 3. Compare the releases.
    comparison_response = client.get(
        "/api/v1/metrics/compare",
        params={
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
        },
    )
    assert comparison_response.status_code == 200, comparison_response.text

    comparison = comparison_response.json()
    assessment = comparison["regression_assessment"]

    assert assessment["status"] == "regression_detected"
    assert assessment["baseline_error_rate"] == 1.0
    assert assessment["candidate_error_rate"] == 25.0
    assert assessment["p_value"] < 0.05

    # 4. Create an investigation.
    investigation_response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Checkout regression after release",
            "question": "Why did checkout errors increase?",
        },
    )
    assert investigation_response.status_code == 201, (
        investigation_response.text
    )
    investigation_id = investigation_response.json()["id"]

    # 5. Link the comparison assessment to the investigation.
    evidence_response = client.post(
        "/api/v1/evidence",
        json={
            "investigation_id": investigation_id,
            "evidence_type": "regression_assessment",
            "title": "Baseline versus candidate regression assessment",
            "description": (
                "Statistical comparison of checkout errors "
                "between two releases."
            ),
            "source": "/api/v1/metrics/compare",
            "data": {
                "baseline": {
                    "release_id": baseline_id,
                },
                "candidate": {
                    "release_id": candidate_id,
                },
                "regression_assessment": assessment,
            },
        },
    )
    assert evidence_response.status_code == 201, evidence_response.text
    evidence_id = evidence_response.json()["id"]

    # 6. Verify the evidence is linked to the investigation.
    detail_response = client.get(
        f"/api/v1/investigations/{investigation_id}",
    )
    assert detail_response.status_code == 200, detail_response.text

    linked_evidence = detail_response.json()["evidence"]
    assert any(item["id"] == evidence_id for item in linked_evidence)

    # 7. Verify that findings use the linked assessment.
    findings_response = client.get(
        f"/api/v1/investigations/{investigation_id}/findings",
    )
    assert findings_response.status_code == 200, findings_response.text

    findings = findings_response.json()
    assert findings["conclusion"] == "regression_signal_detected"
    assert findings["evidence_quality"] == "structured"
    assert findings["valid_assessment_count"] >= 1
    assert any(
        item["evidence_id"] == evidence_id
        for item in findings["evidence_references"]
    )

    # A regression signal is not proof of causation.
    assert any(
        "causation" in limitation.lower()
        or "root cause" in limitation.lower()
        for limitation in findings["limitations"]
    )
