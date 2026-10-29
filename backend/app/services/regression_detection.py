import math
from typing import Any

DEFAULT_MIN_EVENTS = 30
DEFAULT_MIN_ABSOLUTE_INCREASE_PP = 1.0
DEFAULT_ALPHA = 0.05
Z_95 = 1.96


def wilson_interval(
    successes: int,
    trials: int,
    z_score: float = Z_95,
) -> tuple[float, float]:
    """Return a Wilson confidence interval as proportions between 0 and 1."""
    if trials <= 0:
        raise ValueError("trials must be greater than zero")
    if successes < 0 or successes > trials:
        raise ValueError("successes must be between zero and trials")
    if z_score <= 0:
        raise ValueError("z_score must be greater than zero")

    proportion = successes / trials
    z_squared = z_score**2
    denominator = 1 + z_squared / trials

    center = (proportion + z_squared / (2 * trials)) / denominator

    margin = (
        z_score
        * math.sqrt(proportion * (1 - proportion) / trials + z_squared / (4 * trials**2))
        / denominator
    )

    return max(0.0, center - margin), min(1.0, center + margin)


def _two_proportion_p_value(
    baseline_errors: int,
    baseline_total: int,
    candidate_errors: int,
    candidate_total: int,
) -> float | None:
    """Calculate a two-sided pooled two-proportion z-test p-value."""
    total = baseline_total + candidate_total
    pooled_rate = (baseline_errors + candidate_errors) / total

    # Normal approximation requires sufficient expected counts in
    # both the error and non-error groups.
    expected_errors_baseline = baseline_total * pooled_rate
    expected_errors_candidate = candidate_total * pooled_rate
    expected_ok_baseline = baseline_total * (1 - pooled_rate)
    expected_ok_candidate = candidate_total * (1 - pooled_rate)

    expected_counts = (
        expected_errors_baseline,
        expected_errors_candidate,
        expected_ok_baseline,
        expected_ok_candidate,
    )
    if min(expected_counts) < 5:
        return None

    pooled_variance = pooled_rate * (1 - pooled_rate) * (1 / baseline_total + 1 / candidate_total)
    if pooled_variance <= 0:
        return None

    baseline_rate = baseline_errors / baseline_total
    candidate_rate = candidate_errors / candidate_total

    z_score = (candidate_rate - baseline_rate) / math.sqrt(pooled_variance)

    # Two-sided p-value for the standard normal distribution.
    return math.erfc(abs(z_score) / math.sqrt(2))


def detect_error_rate_regression(
    baseline_errors: int,
    baseline_total: int,
    candidate_errors: int,
    candidate_total: int,
    min_events: int = DEFAULT_MIN_EVENTS,
    min_absolute_increase_pp: float = DEFAULT_MIN_ABSOLUTE_INCREASE_PP,
    alpha: float = DEFAULT_ALPHA,
) -> dict[str, Any]:
    """Evaluate whether a candidate release has a meaningful error-rate regression."""
    if baseline_total < 0 or candidate_total < 0:
        raise ValueError("Event totals cannot be negative")
    if baseline_errors < 0 or baseline_errors > baseline_total:
        raise ValueError("Invalid baseline error count")
    if candidate_errors < 0 or candidate_errors > candidate_total:
        raise ValueError("Invalid candidate error count")
    if min_events < 1:
        raise ValueError("min_events must be at least one")
    if min_absolute_increase_pp < 0:
        raise ValueError("The minimum increase cannot be negative")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between zero and one")

    if baseline_total == 0 or candidate_total == 0:
        return {
            "status": "insufficient_data",
            "reason": "Both releases need at least one event.",
            "baseline_error_rate": None,
            "candidate_error_rate": None,
            "change_percentage_points": None,
            "baseline_ci_95": None,
            "candidate_ci_95": None,
            "p_value": None,
        }

    baseline_rate = baseline_errors / baseline_total
    candidate_rate = candidate_errors / candidate_total
    change_pp = (candidate_rate - baseline_rate) * 100

    baseline_ci = wilson_interval(baseline_errors, baseline_total)
    candidate_ci = wilson_interval(candidate_errors, candidate_total)

    result: dict[str, Any] = {
        "status": "inconclusive",
        "reason": None,
        "baseline_error_rate": round(baseline_rate * 100, 4),
        "candidate_error_rate": round(candidate_rate * 100, 4),
        "change_percentage_points": round(change_pp, 4),
        "baseline_ci_95": [
            round(baseline_ci[0] * 100, 4),
            round(baseline_ci[1] * 100, 4),
        ],
        "candidate_ci_95": [
            round(candidate_ci[0] * 100, 4),
            round(candidate_ci[1] * 100, 4),
        ],
        "p_value": None,
        "alpha": alpha,
        "minimum_increase_percentage_points": min_absolute_increase_pp,
    }

    if baseline_total < min_events or candidate_total < min_events:
        result["status"] = "insufficient_data"
        result["reason"] = f"Each release needs at least {min_events} events."
        return result

    # A meaningful regression requires an increase, not merely a
    # statistically detectable change in either direction.
    if change_pp < min_absolute_increase_pp:
        result["status"] = "no_regression_detected"
        result["reason"] = "The observed increase is below the configured practical threshold."
        return result

    p_value = _two_proportion_p_value(
        baseline_errors,
        baseline_total,
        candidate_errors,
        candidate_total,
    )
    result["p_value"] = round(p_value, 6) if p_value is not None else None

    if p_value is None:
        result["status"] = "inconclusive"
        result["reason"] = (
            "Expected error or non-error counts are too small for the normal-approximation test."
        )
    elif p_value < alpha:
        result["status"] = "regression_detected"
        result["reason"] = (
            "The error-rate increase meets the practical threshold "
            "and is statistically significant."
        )
    else:
        result["status"] = "inconclusive"
        result["reason"] = (
            "The observed increase is large enough to investigate, "
            "but the statistical test did not establish significance."
        )

    return result
