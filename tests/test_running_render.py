import pytest

from coros_mcp.running.normalize import normalize_running_workout
from coros_mcp.running.render import render_running_workout
from coros_mcp.running.validate import validate_running_workout
from coros_mcp.running.zones import resolve_zone_range


def test_resolve_zone_range_for_percent_max_hr():
    assert resolve_zone_range("heart_rate_percent_max", "warmup_zone") == (60, 70)


def test_validate_rejects_wrong_zone_family():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {"type": "heart_rate_percent_max", "zone": {"preset": "aerobic_power_zone"}},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="zone preset"):
        validate_running_workout(workout)


def test_render_running_workout_summarizes_interval_session():
    workout = normalize_running_workout(
        {
            "name": "4x1km LT",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "warmup",
                    "target": {"type": "time", "value": 15, "unit": "min"},
                    "intensity": {"type": "none"},
                },
                {
                    "kind": "interval",
                    "repeat": 4,
                    "work": {
                        "action": "work",
                        "target": {"type": "distance", "value": 1000, "unit": "m"},
                        "intensity": {"type": "pace_percent_lthr", "zone": {"preset": "lactate_threshold_zone"}},
                    },
                    "recovery": {
                        "action": "recovery",
                        "target": {"type": "distance", "value": 400, "unit": "m"},
                        "intensity": {"type": "none"},
                    },
                },
            ],
        }
    )

    summary = render_running_workout(workout)
    assert "Warmup 15 min" in summary
    assert "4 x [Work 1000 m / Recovery 400 m]" in summary
