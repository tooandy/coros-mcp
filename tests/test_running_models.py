import pytest

from coros_mcp.running.normalize import normalize_running_workout
from coros_mcp.running.validate import validate_running_workout


def test_normalize_running_workout_builds_interval_and_steps():
    workout = normalize_running_workout(
        {
            "name": "4x1km LT",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "warmup",
                    "target": {"type": "time", "value": 15, "unit": "min"},
                    "intensity": {"type": "heart_rate_percent_max", "zone": {"preset": "warmup_zone"}},
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

    assert workout.name == "4x1km LT"
    assert workout.happen_day == "20260715"
    assert workout.steps[0].action == "warmup"
    assert workout.steps[1].repeat == 4
    assert workout.steps[1].work.action == "work"
    assert workout.steps[1].recovery.action == "recovery"


def test_validate_requires_custom_zone_bounds():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {"type": "pace_percent_lthr", "zone": {"preset": "custom", "low": 95}},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="custom zone"):
        validate_running_workout(workout)


def test_validate_open_target_rejects_value():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "cooldown",
                    "target": {"type": "open", "value": 1},
                    "intensity": {"type": "none"},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="open"):
        validate_running_workout(workout)


def test_normalize_rejects_unknown_step_kind():
    with pytest.raises(ValueError, match="kind"):
        normalize_running_workout(
            {
                "name": "Broken",
                "happen_day": "20260715",
                "steps": [
                    {
                        "kind": "tempo",
                        "action": "work",
                        "target": {"type": "time", "value": 20, "unit": "min"},
                        "intensity": {"type": "none"},
                    }
                ],
            }
        )


def test_validate_rejects_zone_for_absolute_intensity():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {"type": "pace", "zone": {"preset": "warmup_zone"}},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="zone"):
        validate_running_workout(workout)


def test_validate_rejects_range_and_zone_together():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {
                        "type": "pace_percent_lthr",
                        "range": {"low": 4.0, "high": 4.5},
                        "zone": {"preset": "lactate_threshold_zone"},
                    },
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="range.*zone|zone.*range"):
        validate_running_workout(workout)


def test_validate_rejects_percent_intensity_without_range_or_zone():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {"type": "heart_rate_percent_max"},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="range|zone"):
        validate_running_workout(workout)


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ({"type": "distance", "unit": "m"}, "value"),
        ({"type": "distance", "value": 1000}, "unit"),
        ({"type": "time", "unit": "min"}, "value"),
        ({"type": "time", "value": 20}, "unit"),
        ({"type": "training_load", "unit": "tss"}, "value"),
    ],
)
def test_validate_rejects_missing_required_target_fields(target, message):
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": target,
                    "intensity": {"type": "none"},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match=message):
        validate_running_workout(workout)
