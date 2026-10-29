
from fastapi.testclient import TestClient


def test_summary_without_evidence(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Checkout issue",
            "question": "Why did checkout fail?",
        },
    )
    investigation_id = create_response.json()["id"]

    response = client.get(
        f"/api/v1/investigations/{investigation_id}/summary"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["investigation_id"] == investigation_id
    assert data["evidence_count"] == 0
    assert data["evidence"] == []
    assert "no linked evidence" in data["summary"].lower()
    assert data["limitations"]


def test_summary_includes_linked_evidence(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Release regression",
            "question": "Did the release increase errors?",
        },
    )
    investigation_id = create_response.json()["id"]

    evidence_response = client.post(
        "/api/v1/evidence",
        json={
            "investigation_id": investigation_id,
            "evidence_type": "event_sample",
            "title": "Checkout failure sample",
            "description": "An example checkout failure event.",
            "source": "test",
            "data": {"event_name": "checkout_failed"},
        },
    )
    assert evidence_response.status_code == 201

    response = client.get(
        f"/api/v1/investigations/{investigation_id}/summary"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["evidence_count"] == 1
    assert data["evidence"][0]["title"] == "Checkout failure sample"
    assert "root-cause" in data["summary"].lower()


def test_summary_for_missing_investigation_returns_404(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/investigations/999999/summary"
    )

    assert response.status_code == 404
