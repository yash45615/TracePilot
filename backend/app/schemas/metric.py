from typing import Literal

from pydantic import BaseModel, Field


class ReleaseMetrics(BaseModel):
    release_id: int
    release_version: str
    total_events: int = Field(ge=0)
    unique_users: int = Field(ge=0)
    conversion_rate: float = Field(ge=0, le=100)
    error_rate: float = Field(ge=0, le=100)
    average_duration_ms: float | None = Field(default=None, ge=0)


class RegressionAssessment(BaseModel):
    status: Literal[
        "insufficient_data",
        "no_regression_detected",
        "regression_detected",
        "inconclusive",
    ]
    reason: str | None = None
    baseline_error_rate: float | None = None
    candidate_error_rate: float | None = None
    change_percentage_points: float | None = None
    baseline_ci_95: list[float] | None = None
    candidate_ci_95: list[float] | None = None
    p_value: float | None = None
    alpha: float | None = Field(default=None, gt=0, lt=1)
    minimum_increase_percentage_points: float | None = None


class MetricChange(BaseModel):
    baseline: ReleaseMetrics
    candidate: ReleaseMetrics
    conversion_change_percentage_points: float
    error_rate_change_percentage_points: float
    average_duration_change_ms: float | None
    interpretation: list[str]
    regression_assessment: RegressionAssessment | None = None
