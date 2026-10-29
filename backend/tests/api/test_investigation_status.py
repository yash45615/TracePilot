
from fastapi.testclient import TestClient


def create_investigation(client: TestClient) -> int:
    response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Status test",
            "question": "Why did the error rate increase?",
        },
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_status_can_move_from_pending_to_in_progress(
    client: TestClient,
) -> None:
    investigation_id = create_investigation(client)

    response = client.patch(
        f"/api/v1/investigations/{investigation_id}/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_status_can_move_to_completed(client: TestClient) -> None:
    investigation_id = create_investigation(client)

    client.patch(
        f"/api/v1/investigations/{investigation_id}/status",
        json={"status": "in_progress"},
    )
    response = client.patch(
        f"/api/v1/investigations/{investigation_id}/status",
        json={"status": "completed"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_completed_investigation_cannot_be_reopened(
    client: TestClient,
) -> None:
    investigation_id = create_investigation(client)

    client.patch(
        f"/api/v1/investigations/{investigation_id}/status",
        json={"status": "in_progress"},
    )
    client.patch(
        f"/api/v1/investigations/{investigation_id}/status",
        json={"status": "completed"},
    )
    response = client.patch(
        f"/api/v1/investigations/{investigation_id}/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 409


def test_invalid_status_is_rejected(client: TestClient) -> None:
    investigation_id = create_investigation(client)

    response = client.patch(
        f"/api/v1/investigations/{investigation_id}/status",
        json={"status": "unknown"},
    )

    assert response.status_code == 422


def test_missing_investigation_returns_404(
    client: TestClient,
) -> None:
    response = client.patch(
        "/api/v1/investigations/999999/status",
        json={"status": "in_progress"},
    )

    assert response.status_code == 404
