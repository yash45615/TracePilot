from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    Base.metadata.create_all(bind=engine)

    def override_get_db() -> Generator[Session, None, None]:
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.pop(get_db, None)
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def create_release(
    client: TestClient,
    version: str,
    name: str,
) -> int:
    response = client.post(
        "/api/v1/releases",
        json={"version": version, "name": name},
    )
    assert response.status_code in (200, 201), response.text
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
                "event_name": "page_view",
                "user_id": f"user-{release_id}-{index}",
                "release_id": release_id,
                "is_error": index < error_count,
                "duration_ms": 100,
                "properties": {},
            },
        )
        assert response.status_code in (200, 201), response.text


def test_compare_endpoint_detects_significant_regression(
    client: TestClient,
) -> None:
    baseline_id = create_release(client, "1.0.0", "Baseline")
    candidate_id = create_release(client, "1.1.0", "Candidate")

    add_events(client, baseline_id, total=1000, error_count=10)
    add_events(client, candidate_id, total=1000, error_count=50)

    response = client.get(
        "/api/v1/metrics/compare",
        params={
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()

    assessment = body["regression_assessment"]
    assert assessment["status"] == "regression_detected"
    assert assessment["baseline_error_rate"] == 1.0
    assert assessment["candidate_error_rate"] == 5.0
    assert assessment["change_percentage_points"] == 4.0
    assert assessment["p_value"] < 0.05


def test_compare_endpoint_reports_insufficient_data(
    client: TestClient,
) -> None:
    baseline_id = create_release(client, "2.0.0", "Baseline")
    candidate_id = create_release(client, "2.1.0", "Candidate")

    add_events(client, baseline_id, total=10, error_count=1)
    add_events(client, candidate_id, total=10, error_count=5)

    response = client.get(
        "/api/v1/metrics/compare",
        params={
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
        },
    )

    assert response.status_code == 200, response.text
    assessment = response.json()["regression_assessment"]

    assert assessment["status"] == "insufficient_data"
    assert assessment["p_value"] is None


def test_compare_endpoint_rejects_same_release(
    client: TestClient,
) -> None:
    release_id = create_release(client, "3.0.0", "Release")

    response = client.get(
        "/api/v1/metrics/compare",
        params={
            "baseline_id": release_id,
            "candidate_id": release_id,
        },
    )

    assert response.status_code == 422


def test_compare_endpoint_returns_404_for_missing_release(
    client: TestClient,
) -> None:
    response = client.get(
        "/api/v1/metrics/compare",
        params={
            "baseline_id": 999,
            "candidate_id": 1000,
        },
    )

    assert response.status_code == 404


def test_release_comparison_persists_evidence(client):
    baseline_response = client.post(
        "/api/v1/releases",
        json={"version": "evidence-baseline-1", "name": "Baseline"},
    )
    candidate_response = client.post(
        "/api/v1/releases",
        json={"version": "evidence-candidate-1", "name": "Candidate"},
    )

    assert baseline_response.status_code == 201
    assert candidate_response.status_code == 201

    baseline_id = baseline_response.json()["id"]
    candidate_id = candidate_response.json()["id"]

    comparison_response = client.get(
        "/api/v1/metrics/compare",
        params={
            "baseline_id": baseline_id,
            "candidate_id": candidate_id,
        },
    )

    assert comparison_response.status_code == 200
    comparison = comparison_response.json()
    assert "regression_assessment" in comparison

    evidence_response = client.get("/api/v1/evidence")

    assert evidence_response.status_code == 200
    evidence_records = evidence_response.json()

    matching_records = [
        record
        for record in evidence_records
        if record["evidence_type"] == "regression_assessment"
        and record["data"]["baseline"]["release_id"] == baseline_id
        and record["data"]["candidate"]["release_id"] == candidate_id
    ]

    assert len(matching_records) == 1
    assert matching_records[0]["source"] == "/api/v1/metrics/compare"
    assert "regression_assessment" in matching_records[0]["data"]
