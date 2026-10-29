from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import ProductEvent, Release
from app.services.release_comparison import compare_releases


def test_release_comparison_calculates_metric_changes() -> None:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        baseline = Release(version="1.0.0", name="Baseline")
        candidate = Release(version="1.1.0", name="Candidate")
        db.add_all([baseline, candidate])
        db.flush()

        now = datetime.now(UTC)

        db.add_all(
            [
                ProductEvent(
                    event_name="page_view",
                    user_id="user-1",
                    release_id=baseline.id,
                    occurred_at=now,
                    duration_ms=100,
                    is_error=False,
                    properties={},
                ),
                ProductEvent(
                    event_name="conversion",
                    user_id="user-1",
                    release_id=baseline.id,
                    occurred_at=now,
                    duration_ms=120,
                    is_error=False,
                    properties={},
                ),
                ProductEvent(
                    event_name="page_view",
                    user_id="user-2",
                    release_id=baseline.id,
                    occurred_at=now,
                    duration_ms=80,
                    is_error=False,
                    properties={},
                ),
                ProductEvent(
                    event_name="page_view",
                    user_id="user-1",
                    release_id=candidate.id,
                    occurred_at=now,
                    duration_ms=200,
                    is_error=True,
                    properties={},
                ),
                ProductEvent(
                    event_name="page_view",
                    user_id="user-2",
                    release_id=candidate.id,
                    occurred_at=now,
                    duration_ms=300,
                    is_error=True,
                    properties={},
                ),
                ProductEvent(
                    event_name="conversion",
                    user_id="user-2",
                    release_id=candidate.id,
                    occurred_at=now,
                    duration_ms=250,
                    is_error=False,
                    properties={},
                ),
            ]
        )
        db.commit()

        result = compare_releases(db, baseline, candidate)

        assert result.baseline.conversion_rate == 50.0
        assert result.candidate.conversion_rate == 50.0
        assert result.baseline.error_rate == 0.0
        assert result.candidate.error_rate == 66.67
        assert result.conversion_change_percentage_points == 0.0
        assert result.error_rate_change_percentage_points == 66.67
        assert result.average_duration_change_ms == 150.0

    Base.metadata.drop_all(engine)
    engine.dispose()
