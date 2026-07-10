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
    assert len(program["exercises"]) == 5
    assert [ex["exerciseType"] for ex in program["exercises"]] == [1, 0, 2, 4, 3]

    group, work, recovery = program["exercises"][1:4]
    assert group["isGroup"] is True
    assert work["groupId"] == str(group["id"])
    assert recovery["groupId"] == str(group["id"])
    assert work["intensityType"] == 3
    assert work["intensityValue"] == 100
    assert work["intensityValueExtend"] == 105


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
