
import json
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

BASE_URL = "http://127.0.0.1:8000"

RELEASES = {
    "baseline": {"id": 1, "version": "1.0.0"},
    "candidate": {"id": 2, "version": "1.1.0"},
}


def post_event(payload: dict) -> dict:
    """Create one event through the TracePilot API."""
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        f"{BASE_URL}/api/v1/events",
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(
            f"Event creation failed (HTTP {exc.code}): {details}"
        ) from exc


def build_event(
    release_id: int,
    release_label: str,
    index: int,
    is_error: bool,
) -> dict:
    """Build a deterministic synthetic product event."""
    now = datetime.now(timezone.utc)
    occurred_at = now - timedelta(minutes=index)

    # Keep normal and error durations visibly different.
    duration_ms = (
        800 + (index % 5) * 150
        if is_error
        else 100 + (index % 5) * 20
    )

    return {
        "event_name": "checkout_completed" if not is_error else "checkout_failed",
        "user_id": f"tracepilot-{release_label}-user-{index:03d}",
        "release_id": release_id,
        "occurred_at": occurred_at.isoformat(),
        "duration_ms": duration_ms,
        "is_error": is_error,
        "properties": {
            "seed_batch": "release-regression-demo-v1",
            "release_label": release_label,
            "scenario": "synthetic_regression_test",
        },
    }


def main() -> None:
    # Check that the API is running and that the expected releases exist.
    with urllib.request.urlopen(
        f"{BASE_URL}/api/v1/health", timeout=10
    ) as response:
        health = json.loads(response.read().decode("utf-8"))

    print(f"Connected to TracePilot: {health}")

    with urllib.request.urlopen(
        f"{BASE_URL}/api/v1/releases", timeout=10
    ) as response:
        releases = json.loads(response.read().decode("utf-8"))

    release_by_id = {int(release["id"]): release for release in releases}

    for label, expected in RELEASES.items():
        actual = release_by_id.get(expected["id"])
        if not actual:
            raise RuntimeError(
                f"Release ID {expected['id']} not found. "
                "Check the release IDs before seeding."
            )

        if actual["version"] != expected["version"]:
            raise RuntimeError(
                f"Release ID {expected['id']} has version "
                f"{actual['version']!r}, not {expected['version']!r}."
            )

    scenarios = [
        # Baseline: 1 error out of 30 events.
        ("baseline", 1),
        # Candidate: 12 errors out of 30 events.
        ("candidate", 12),
    ]

    created = {"baseline": 0, "candidate": 0}

    for label, error_count in scenarios:
        release_id = RELEASES[label]["id"]

        print(f"\nSeeding {label} release ({RELEASES[label]['version']})")

        for index in range(30):
            is_error = index < error_count
            payload = build_event(
                release_id=release_id,
                release_label=label,
                index=index,
                is_error=is_error,
            )

            result = post_event(payload)
            created[label] += 1

            if created[label] % 10 == 0:
                print(f"  Created {created[label]}/30 events")

        print(
            f"  Finished: {created[label]} events, "
            f"{error_count} errors"
        )

    print("\nSeed complete.")
    print(f"Baseline events created:  {created['baseline']}")
    print(f"Candidate events created: {created['candidate']}")
    print("Expected baseline error rate:  3.33%")
    print("Expected candidate error rate: 40.00%")
    print("Expected error-rate increase: 36.67 percentage points")
    print("\nOpen http://127.0.0.1:8000/docs to inspect the API.")


if __name__ == "__main__":
    main()
