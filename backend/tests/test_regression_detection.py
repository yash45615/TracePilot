import pytest

from app.services.regression_detection import (
    detect_error_rate_regression,
    wilson_interval,
)


def test_wilson_interval_contains_observed_rate():
    lower, upper = wilson_interval(10, 100)

    assert lower < 0.10 < upper
    assert 0 <= lower <= upper <= 1


def test_detects_large_significant_regression():
    result = detect_error_rate_regression(
        baseline_errors=100,
        baseline_total=10_000,
        candidate_errors=300,
        candidate_total=10_000,
    )

    assert result["status"] == "regression_detected"
    assert result["change_percentage_points"] == 2.0
    assert result["p_value"] is not None
    assert result["p_value"] < 0.05


def test_insufficient_sample_size_is_not_a_regression():
    result = detect_error_rate_regression(
        baseline_errors=2,
        baseline_total=10,
        candidate_errors=5,
        candidate_total=10,
    )

    assert result["status"] == "insufficient_data"
    assert result["p_value"] is None


def test_small_error_counts_are_inconclusive():
    result = detect_error_rate_regression(
        baseline_errors=0,
        baseline_total=100,
        candidate_errors=2,
        candidate_total=100,
    )

    assert result["status"] == "inconclusive"
    assert result["p_value"] is None


def test_increase_below_practical_threshold_is_not_flagged():
    result = detect_error_rate_regression(
        baseline_errors=100,
        baseline_total=10_000,
        candidate_errors=110,
        candidate_total=10_000,
    )

    assert result["status"] == "no_regression_detected"


def test_rejects_invalid_error_counts():
    with pytest.raises(ValueError, match="Invalid baseline error count"):
        detect_error_rate_regression(
            baseline_errors=11,
            baseline_total=10,
            candidate_errors=1,
            candidate_total=100,
        )


def test_zero_events_return_insufficient_data():
    result = detect_error_rate_regression(
        baseline_errors=0,
        baseline_total=0,
        candidate_errors=0,
        candidate_total=100,
    )

    assert result["status"] == "insufficient_data"
