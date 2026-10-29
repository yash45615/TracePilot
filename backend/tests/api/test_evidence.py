
from fastapi.testclient import TestClient


def test_create_evidence(client: TestClient) -> None:
    response = client.post(
        "/api/v1/evidence",
        json={
            "evidence_type": "release_metrics",
            "title": "Baseline release metrics",
            "description": "Metrics collected for the baseline release.",
            "source": "GET /api/v1/metrics/release",
            "data": {
                "release_version": "1.0.0",
                "total_events": 100,
                "error_rate": 2.0,
            },
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["id"] > 0
    assert body["evidence_type"] == "release_metrics"
    assert body["title"] == "Baseline release metrics"
    assert body["data"]["total_events"] == 100
    assert body["investigation_id"] is None


def test_list_evidence(client: TestClient) -> None:
    for title in ["Evidence A", "Evidence B"]:
        response = client.post(
            "/api/v1/evidence",
            json={
                "evidence_type": "event_sample",
                "title": title,
                "description": f"Description for {title}.",
                "source": "test",
                "data": {},
            },
        )
        assert response.status_code == 201

    response = client.get("/api/v1/evidence")

    assert response.status_code == 200
    titles = [item["title"] for item in response.json()]
    assert "Evidence A" in titles
    assert "Evidence B" in titles


def test_get_evidence_by_id(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/evidence",
        json={
            "evidence_type": "regression_assessment",
            "title": "Regression check",
            "description": "Error-rate comparison.",
            "source": "test",
            "data": {"status": "inconclusive"},
        },
    )
    assert create_response.status_code == 201
    evidence_id = create_response.json()["id"]

    response = client.get(f"/api/v1/evidence/{evidence_id}")

    assert response.status_code == 200
    assert response.json()["id"] == evidence_id
    assert response.json()["data"]["status"] == "inconclusive"


def test_get_missing_evidence_returns_404(client: TestClient) -> None:
    response = client.get("/api/v1/evidence/999999")

    assert response.status_code == 404


def test_invalid_evidence_type_returns_422(client: TestClient) -> None:
    response = client.post(
        "/api/v1/evidence",
        json={
            "evidence_type": "invalid_type",
            "title": "Invalid evidence",
            "description": "This should be rejected.",
            "source": "test",
            "data": {},
        },
    )

    assert response.status_code == 422


def test_missing_investigation_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/evidence",
        json={
            "investigation_id": 999999,
            "evidence_type": "release_metrics",
            "title": "Unlinked evidence",
            "description": "Investigation does not exist.",
            "source": "test",
            "data": {},
        },
    )

    assert response.status_code == 404
