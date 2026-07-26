import pytest

from coros_mcp.running.compile import compile_running_workout
from coros_mcp.running.normalize import normalize_running_workout


def test_compile_running_workout_builds_group_and_overview():
    workout = normalize_running_workout(
        {
            "name": "4x1km LT",
            "description": "Threshold repeats",
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
                        "intensity": {
                            "type": "pace_percent_lthr",
                            "zone": {"preset": "lactate_threshold_zone"},
                        },
                    },
                    "recovery": {
                        "action": "recovery",
                        "target": {"type": "distance", "value": 400, "unit": "m"},
                        "intensity": {"type": "none"},
                    },
                },
                {
                    "kind": "step",
                    "action": "cooldown",
                    "target": {"type": "time", "value": 10, "unit": "min"},
                    "intensity": {"type": "none"},
                },
            ],
        }
    )

    program = compile_running_workout(workout)

    assert program["sportType"] == 1
    assert program["overview"] == "Threshold repeats"
    assert program["subType"] == 65535
    assert program["duration"] == 25 * 60
    assert program["referExercise"]["hrType"] == 0
    assert len(program["exercises"]) == 5
    assert [ex["exerciseType"] for ex in program["exercises"]] == [1, 0, 2, 4, 3]

    group, work, recovery = program["exercises"][1:4]
    assert group["isGroup"] is True
    assert group["targetType"] == 0
    assert group["targetValue"] == 0
    assert work["groupId"] == str(group["id"])
    assert recovery["groupId"] == str(group["id"])
    assert work["exerciseType"] == 2
    assert recovery["exerciseType"] == 4
    assert work["intensityType"] == 3
    assert work["isIntensityPercent"] is True
    assert work["intensityPercent"] == 100_000
    assert work["intensityPercentExtend"] == 105_000
    assert work["intensityValue"] == 0
    assert work["intensityValueExtend"] == 0


def test_compile_running_workout_uses_interval_round_duration_for_time_groups():
    workout = normalize_running_workout(
        {
            "name": "6x hard/easy",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "interval",
                    "repeat": 6,
                    "work": {
                        "action": "work",
                        "target": {"type": "time", "value": 2, "unit": "min"},
                        "intensity": {"type": "none"},
                    },
                    "recovery": {
                        "action": "recovery",
                        "target": {"type": "time", "value": 1, "unit": "min"},
                        "intensity": {"type": "none"},
                    },
                }
            ],
        }
    )

    program = compile_running_workout(workout)

    group, work, recovery = program["exercises"]
    assert group["isGroup"] is True
    assert group["targetType"] == 2
    assert group["targetValue"] == 180
    assert work["targetValue"] == 120
    assert recovery["targetValue"] == 60
    assert work["exerciseType"] == 2
    assert recovery["exerciseType"] == 4


def test_compile_running_workout_uses_structural_header_for_open_interval_groups():
    workout = normalize_running_workout(
        {
            "name": "Open recoveries",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "interval",
                    "repeat": 5,
                    "work": {
                        "action": "work",
                        "target": {"type": "time", "value": 90, "unit": "sec"},
                        "intensity": {"type": "none"},
                    },
                    "recovery": {
                        "action": "recovery",
                        "target": {"type": "open"},
                        "intensity": {"type": "none"},
                    },
                }
            ],
        }
    )

    program = compile_running_workout(workout)

    group, work, recovery = program["exercises"]
    assert group["isGroup"] is True
    assert group["targetType"] == 0
    assert group["targetValue"] == 0
    assert work["targetType"] == 2
    assert recovery["targetType"] == 1


def test_compile_running_workout_sets_program_hrtype_for_hr_semantics():
    workout = normalize_running_workout(
        {
            "name": "HR run",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 30, "unit": "min"},
                    "intensity": {"type": "heart_rate", "range": {"low": 140, "high": 150}},
                }
            ],
        }
    )

    program = compile_running_workout(workout)

    assert program["exercises"][0]["hrType"] == 2
    assert program["referExercise"]["hrType"] == 3


@pytest.mark.parametrize(
    ("intensity_type", "expected_hr_type"),
    [
        ("heart_rate_percent_max", 1),
        ("heart_rate_percent_reserve", 2),
        ("heart_rate_percent_lthr", 3),
    ],
)
def test_compile_running_workout_encodes_heart_rate_percent_ranges_as_percent_fields(
    intensity_type, expected_hr_type
):
    workout = normalize_running_workout(
        {
            "name": "HR percent run",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 30, "unit": "min"},
                    "intensity": {
                        "type": intensity_type,
                        "range": {"low": 75, "high": 85},
                    },
                }
            ],
        }
    )

    exercise = compile_running_workout(workout)["exercises"][0]

    assert exercise["hrType"] == expected_hr_type
    assert exercise["intensityType"] == 2
    assert exercise["isIntensityPercent"] is True
    assert exercise["intensityPercent"] == 75_000
    assert exercise["intensityPercentExtend"] == 85_000
    assert exercise["intensityValue"] == 0
    assert exercise["intensityValueExtend"] == 0


def test_compile_running_workout_encodes_pace_percent_ranges_as_percent_fields():
    workout = normalize_running_workout(
        {
            "name": "Pace percent run",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {
                        "type": "pace_percent_lthr",
                        "range": {"low": 98, "high": 102},
                    },
                }
            ],
        }
    )

    exercise = compile_running_workout(workout)["exercises"][0]

    assert exercise["hrType"] == 0
    assert exercise["intensityType"] == 3
    assert exercise["isIntensityPercent"] is True
    assert exercise["intensityPercent"] == 98_000
    assert exercise["intensityPercentExtend"] == 102_000
    assert exercise["intensityValue"] == 0
    assert exercise["intensityValueExtend"] == 0


def test_compile_running_workout_sets_default_percent_fields_for_absolute_intensity():
    workout = normalize_running_workout(
        {
            "name": "Absolute pace run",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {
                        "type": "pace",
                        "range": {"low": 240000, "high": 255000},
                    },
                }
            ],
        }
    )

    exercise = compile_running_workout(workout)["exercises"][0]

    assert exercise["isIntensityPercent"] is False
    assert exercise["intensityPercent"] == 0
    assert exercise["intensityPercentExtend"] == 0
    assert exercise["intensityValue"] == 240000
    assert exercise["intensityValueExtend"] == 255000


def test_compile_running_workout_supports_training_load_target():
    workout = normalize_running_workout(
        {
            "name": "Load target",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "training_load", "value": 100},
                    "intensity": {"type": "none"},
                }
            ],
        }
    )

    exercise = compile_running_workout(workout)["exercises"][0]

    assert exercise["targetType"] == 6
    assert exercise["targetValue"] == 100


@pytest.mark.parametrize(
    ("target", "message"),
    [
        ({"type": "training_load", "value": 100.9}, "training_load.*integer|integer.*training_load"),
        ({"type": "training_load", "value": True}, "training_load.*integer|integer.*training_load"),
    ],
)
def test_compile_running_workout_rejects_non_integer_training_load_targets(target, message):
    workout = normalize_running_workout(
        {
            "name": "Invalid load target",
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
        compile_running_workout(workout)


def test_compile_running_workout_supports_effort_pace_percent_threshold():
    workout = normalize_running_workout(
        {
            "name": "Effort pace threshold test",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {
                        "type": "effort_pace_percent_threshold",
                        "zone": {"preset": "aerobic_power_zone"},
                    },
                }
            ],
        }
    )

    exercise = compile_running_workout(workout)["exercises"][0]

    assert exercise["intensityType"] == 8
    assert exercise["isIntensityPercent"] is True
    assert exercise["intensityPercent"] == 85_100
    assert exercise["intensityPercentExtend"] == 92_600
    assert exercise["intensityValue"] == 0
    assert exercise["intensityValueExtend"] == 0


def test_compile_running_workout_uses_sample_backed_aerobic_power_zone_for_lthr_pace():
    workout = normalize_running_workout(
        {
            "name": "LT aerobic power test",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {
                        "type": "pace_percent_lthr",
                        "zone": {"preset": "aerobic_power_zone"},
                    },
                }
            ],
        }
    )

    exercise = compile_running_workout(workout)["exercises"][0]

    assert exercise["intensityType"] == 3
    assert exercise["isIntensityPercent"] is True
    assert exercise["intensityPercent"] == 85_100
    assert exercise["intensityPercentExtend"] == 92_600


def test_compile_running_workout_does_not_apply_pace_zone_sample_to_hr_reserve():
    workout = normalize_running_workout(
        {
            "name": "HRR aerobic power test",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {
                        "type": "heart_rate_percent_reserve",
                        "zone": {"preset": "aerobic_power_zone"},
                    },
                }
            ],
        }
    )

    exercise = compile_running_workout(workout)["exercises"][0]

    assert exercise["intensityType"] == 2
    assert exercise["hrType"] == 2
    assert exercise["isIntensityPercent"] is True
    assert exercise["intensityPercent"] == 95_000
    assert exercise["intensityPercentExtend"] == 100_000


def test_compile_running_workout_supports_effort_pace_absolute_range():
    workout = normalize_running_workout(
        {
            "name": "Effort pace direct test",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "open"},
                    "intensity": {
                        "type": "effort_pace",
                        "range": {"low": 300000, "high": 360000},
                    },
                }
            ],
        }
    )

    exercise = compile_running_workout(workout)["exercises"][0]

    assert exercise["targetType"] == 1
    assert exercise["targetValue"] == 0
    assert exercise["intensityType"] == 8
    assert exercise["isIntensityPercent"] is False
    assert exercise["intensityValue"] == 300000
    assert exercise["intensityValueExtend"] == 360000


def test_compile_rejects_open_ended_direct_range_until_supported():
    workout = normalize_running_workout(
        {
            "name": "Open-ended pace test",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "time", "value": 20, "unit": "min"},
                    "intensity": {
                        "type": "pace",
                        "range": {"low": 4.0},
                    },
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="open-ended"):
        compile_running_workout(workout)


def test_compile_rejects_open_ended_effort_pace_range_until_supported():
    workout = normalize_running_workout(
        {
            "name": "Open-ended effort pace test",
            "happen_day": "20260715",
            "steps": [
                {
                    "kind": "step",
                    "action": "work",
                    "target": {"type": "open"},
                    "intensity": {
                        "type": "effort_pace",
                        "range": {"low": 300000},
                    },
                }
            ],
        }
    )

    with pytest.raises(ValueError, match="open-ended"):
        compile_running_workout(workout)
