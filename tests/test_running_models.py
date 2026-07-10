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


def test_validate_rejects_non_numeric_training_load_value():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "training_load", "value": "100"},
                    "intensity": {"type": "none"},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="training_load.*numeric|numeric.*training_load"):
        validate_running_workout(workout)


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ({"type": "distance", "value": "1000", "unit": "m"}, "distance.*numeric|numeric.*distance"),
        ({"type": "time", "value": "20", "unit": "min"}, "time.*numeric|numeric.*time"),
    ],
)
def test_validate_rejects_non_numeric_distance_and_time_values(target, message):
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


def test_validate_rejects_direct_numeric_intensity_without_range():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {"type": "heart_rate"},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="heart_rate.*range|range.*heart_rate"):
        validate_running_workout(workout)


def test_validate_rejects_direct_numeric_intensity_without_range_low():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {"type": "pace", "range": {"low": None, "high": 4.5}},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="range.low"):
        validate_running_workout(workout)


@pytest.mark.parametrize(
    ("intensity", "message"),
    [
        (
            {
                "type": "pace_percent_lthr",
                "range": {"low": "4.0", "high": 4.5},
            },
            "range.*numeric|numeric.*range",
        ),
        (
            {
                "type": "pace_percent_lthr",
                "zone": {"preset": "custom", "low": 95, "high": "90"},
            },
            "custom zone.*numeric|numeric.*custom zone",
        ),
        (
            {
                "type": "pace_percent_lthr",
                "zone": {"preset": "custom", "low": 95, "high": 90},
            },
            "high.*low|low.*high",
        ),
    ],
)
def test_validate_rejects_non_numeric_or_reversed_percent_bounds(intensity, message):
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": intensity,
                }
            ],
        }
    )

    with pytest.raises(ValueError, match=message):
        validate_running_workout(workout)


def test_validate_rejects_reversed_direct_numeric_bounds():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {"type": "pace", "range": {"low": 4.5, "high": 4.0}},
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="high.*low|low.*high"):
        validate_running_workout(workout)


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ({"type": "distance", "value": 1000, "unit": "km"}, "unsupported unit|supported unit"),
    ],
)
def test_validate_rejects_unsupported_distance_and_time_units(target, message):
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


def test_validate_accepts_time_unit_sec():
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "sec"},
                    "intensity": {"type": "none"},
                }
            ],
        }
    )

    validate_running_workout(workout)


@pytest.mark.parametrize(
    ("intensity", "message"),
    [
        ({"type": "heart_rate_percent_max", "zone": {"preset": "not_real_zone"}}, "preset"),
        ({"type": "heart_rate_percent_max", "zone": {"preset": "aerobic_power_zone"}}, "heart_rate_percent_max"),
        ({"type": "pace_percent_lthr", "zone": {"preset": "warmup_zone"}}, "pace_percent_lthr"),
    ],
)
def test_validate_rejects_invalid_percent_zone_preset_or_family(intensity, message):
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": intensity,
                }
            ],
        }
    )

    with pytest.raises(ValueError, match=message):
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


@pytest.mark.parametrize(
    ("step", "message"),
    [
        (
            {
                "kind": "step",
                "action": "tempo",
                "target": {"type": "time", "value": 20, "unit": "min"},
                "intensity": {"type": "none"},
            },
            "action",
        ),
        (
            {
                "kind": "step",
                "action": "work",
                "target": {"type": "pace", "value": 20},
                "intensity": {"type": "none"},
            },
            "target.*type|type.*target",
        ),
        (
            {
                "kind": "step",
                "action": "work",
                "target": {"type": "time", "value": 20, "unit": "min"},
                "intensity": {"type": "speed"},
            },
            "intensity.*type|type.*intensity",
        ),
    ],
)
def test_validate_rejects_unknown_enum_values(step, message):
    workout = normalize_running_workout(
        {
            "name": "Broken",
            "happen_day": "20260715",
            "steps": [step],
        }
    )

    with pytest.raises(ValueError, match=message):
        validate_running_workout(workout)


@pytest.mark.parametrize("repeat", [1.9, True, "4"])
def test_normalize_rejects_non_integer_interval_repeat(repeat):
    with pytest.raises(ValueError, match="repeat"):
        normalize_running_workout(
            {
                "name": "Broken",
                "happen_day": "20260715",
                "steps": [
                    {
                        "kind": "interval",
                        "repeat": repeat,
                        "work": {
                            "action": "work",
                            "target": {"type": "time", "value": 20, "unit": "min"},
                            "intensity": {"type": "none"},
                        },
                        "recovery": {
                            "action": "recovery",
                            "target": {"type": "time", "value": 5, "unit": "min"},
                            "intensity": {"type": "none"},
                        },
                    }
                ],
            }
        )
