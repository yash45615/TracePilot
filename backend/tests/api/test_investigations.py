
from fastapi.testclient import TestClient


def test_create_investigation(client: TestClient) -> None:
    response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Investigate checkout errors",
            "question": "Why did the checkout error rate increase?",
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Investigate checkout errors"
    assert data["question"] == "Why did the checkout error rate increase?"
    assert data["status"] == "pending"
    assert isinstance(data["id"], int)


def test_list_investigations(client: TestClient) -> None:
    client.post(
        "/api/v1/investigations",
        json={
            "title": "Investigation one",
            "question": "What changed?",
        },
    )
    client.post(
        "/api/v1/investigations",
        json={
            "title": "Investigation two",
            "question": "Why did latency increase?",
        },
    )

    response = client.get("/api/v1/investigations")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert {item["title"] for item in data} == {
        "Investigation one",
        "Investigation two",
    }


def test_get_investigation_detail(client: TestClient) -> None:
    create_response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Release regression",
            "question": "Did the latest release introduce errors?",
        },
    )
    investigation_id = create_response.json()["id"]

    response = client.get(f"/api/v1/investigations/{investigation_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == investigation_id
    assert data["title"] == "Release regression"
    assert data["evidence"] == []


def test_get_missing_investigation_returns_404(
    client: TestClient,
) -> None:
    response = client.get("/api/v1/investigations/999999")

    assert response.status_code == 404


def test_investigation_detail_includes_linked_evidence(
    client: TestClient,
) -> None:
    create_response = client.post(
        "/api/v1/investigations",
        json={
            "title": "Checkout investigation",
            "question": "What caused the checkout failure?",
        },
    )
    investigation_id = create_response.json()["id"]

    evidence_response = client.post(
        "/api/v1/evidence",
        json={
            "investigation_id": investigation_id,
            "evidence_type": "event_sample",
            "title": "Checkout error sample",
            "description": "An event recorded during checkout failure.",
            "source": "test",
            "data": {"event_name": "checkout_failed"},
        },
    )

    assert evidence_response.status_code == 201

    detail_response = client.get(
        f"/api/v1/investigations/{investigation_id}"
    )

    assert detail_response.status_code == 200
    evidence = detail_response.json()["evidence"]
    assert len(evidence) == 1
    assert evidence[0]["title"] == "Checkout error sample"
    assert evidence[0]["investigation_id"] == investigation_id
