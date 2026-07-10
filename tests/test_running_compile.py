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
    assert [ex["exerciseType"] for ex in program["exercises"]] == [1, 0, 2, 2, 3]

    group, work, recovery = program["exercises"][1:4]
    assert group["isGroup"] is True
    assert work["groupId"] == str(group["id"])
    assert recovery["groupId"] == str(group["id"])
    assert work["exerciseType"] == 2
    assert recovery["exerciseType"] == 2
    assert work["intensityType"] == 3
    assert work["intensityValue"] == 100
    assert work["intensityValueExtend"] == 105


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
    assert recovery["exerciseType"] == 2


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


def test_compile_running_workout_rejects_training_load_until_supported():
    workout = normalize_running_workout(
        {
            "name": "TL test",
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

    with pytest.raises(ValueError, match="training_load"):
        compile_running_workout(workout)


def test_compile_running_workout_rejects_unsupported_effort_pace_semantics():
    workout = normalize_running_workout(
        {
            "name": "Effort pace test",
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

    with pytest.raises(ValueError, match="effort_pace_percent_threshold"):
        compile_running_workout(workout)
