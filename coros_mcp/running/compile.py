from __future__ import annotations

from coros_mcp.running.models import IntensitySpec, IntervalNode, RunningWorkout, StepNode, TargetSpec
from coros_mcp.running.validate import validate_running_workout
from coros_mcp.running.zones import resolve_zone_range

_ACTION_EXERCISE_TYPES = {
    "warmup": 1,
    "work": 2,
    "recovery": 4,
    "cooldown": 3,
}

_HR_PERCENT_INTENSITY_TYPES = {
    "heart_rate_percent_max",
    "heart_rate_percent_reserve",
    "heart_rate_percent_lthr",
}

_HR_INTENSITY_TYPES = _HR_PERCENT_INTENSITY_TYPES | {"heart_rate"}

_UNSUPPORTED_INTENSITY_TYPES = {
    "effort_pace",
    "effort_pace_percent_threshold",
}


def _compile_target(target: TargetSpec) -> tuple[int, int, int]:
    if target.type == "time":
        multiplier = 60 if target.unit == "min" else 1
        return 2, int(target.value * multiplier), 0
    if target.type == "distance":
        return 5, int(target.value * 100), 1
    if target.type == "open":
        return 0, 0, 0
    raise ValueError(f"target type {target.type!r} is not yet supported by the COROS compiler")


def _compile_intensity(intensity: IntensitySpec) -> dict:
    if intensity.type == "none":
        return {
            "hrType": 0,
            "intensityDisplayUnit": "0",
            "intensityMultiplier": 0,
            "intensityPercentExtend": 0,
            "intensityType": 0,
            "intensityValue": 0,
            "intensityValueExtend": 0,
        }
    if intensity.type in _UNSUPPORTED_INTENSITY_TYPES:
        raise ValueError(
            f"intensity type {intensity.type!r} is not yet supported by the COROS compiler"
        )

    if intensity.zone is not None:
        if intensity.zone.preset == "custom":
            low = int(intensity.zone.low)
            high = int(intensity.zone.high)
        else:
            low, high = resolve_zone_range(intensity.type, intensity.zone.preset)
    elif intensity.range is not None:
        low = int(intensity.range.low)
        high = int(intensity.range.high if intensity.range.high is not None else intensity.range.low)
    else:
        raise ValueError(f"intensity type {intensity.type!r} is missing range or zone")

    if intensity.type in _HR_PERCENT_INTENSITY_TYPES or intensity.type == "heart_rate":
        return {
            "hrType": 2,
            "intensityDisplayUnit": "0",
            "intensityMultiplier": 0,
            "intensityPercentExtend": 0,
            "intensityType": 2,
            "intensityValue": low,
            "intensityValueExtend": high,
        }
    if intensity.type == "pace_percent_lthr" or intensity.type == "pace":
        return {
            "hrType": 0,
            "intensityDisplayUnit": "1",
            "intensityMultiplier": 1000,
            "intensityPercentExtend": 0,
            "intensityType": 3,
            "intensityValue": low,
            "intensityValueExtend": high,
        }
    if intensity.type == "power":
        return {
            "hrType": 0,
            "intensityDisplayUnit": "0",
            "intensityMultiplier": 0,
            "intensityPercentExtend": 0,
            "intensityType": 6,
            "intensityValue": low,
            "intensityValueExtend": high,
        }
    if intensity.type == "cadence":
        return {
            "hrType": 0,
            "intensityDisplayUnit": "0",
            "intensityMultiplier": 0,
            "intensityPercentExtend": 0,
            "intensityType": 7,
            "intensityValue": low,
            "intensityValueExtend": high,
        }

    raise ValueError(f"intensity type {intensity.type!r} is not yet supported by the COROS compiler")


def _refer_exercise_hr_type(workout: RunningWorkout) -> int:
    def _step_uses_hr(intensity: IntensitySpec) -> bool:
        return intensity.type in _HR_INTENSITY_TYPES

    for node in workout.steps:
        if isinstance(node, IntervalNode):
            if _step_uses_hr(node.work.intensity) or _step_uses_hr(node.recovery.intensity):
                return 3
        elif _step_uses_hr(node.intensity):
            return 3
    return 0


def _compile_interval_group_target(interval: IntervalNode) -> tuple[int, int]:
    work_target_type, work_target_value, work_display_unit = _compile_target(interval.work.target)
    recovery_target_type, recovery_target_value, recovery_display_unit = _compile_target(interval.recovery.target)

    if work_target_type == 0 or recovery_target_type == 0:
        raise ValueError("interval group target cannot be derived from open targets")
    if work_target_type != recovery_target_type or work_display_unit != recovery_display_unit:
        raise ValueError("interval group target requires matching work/recovery target types")

    return work_target_type, work_target_value + recovery_target_value


def _base_exercise(step: StepNode, exercise_id: int, exercise_type: int, sort_no: int, group_id: str) -> tuple[dict, int]:
    target_type, target_value, target_display_unit = _compile_target(step.target)
    exercise = {
        "exerciseKind": 0,
        "exerciseType": exercise_type,
        "gradeSystem": 0,
        "groupId": group_id,
        "id": exercise_id,
        "isGroup": False,
        "name": step.action.capitalize(),
        "onsightGradeOffset": 0,
        "originId": "0",
        "overview": "",
        "packageTime": 0,
        "restType": 3,
        "restValue": 0,
        "sets": 1,
        "sortNo": sort_no,
        "sourceId": "0",
        "sportType": 1,
        "subType": 0,
        "targetDisplayUnit": target_display_unit,
        "targetType": target_type,
        "targetValue": target_value,
        **_compile_intensity(step.intensity),
    }
    duration_seconds = target_value if target_type == 2 else 0
    return exercise, duration_seconds


def compile_running_workout(workout: RunningWorkout) -> dict:
    validate_running_workout(workout)

    exercises: list[dict] = []
    total_seconds = 0
    top_index = 0
    exercise_id = 0

    for node in workout.steps:
        top_index += 1
        group_sort = 16777216 * top_index

        if isinstance(node, IntervalNode):
            exercise_id += 1
            group_id = exercise_id
            group_target_type, group_target_value = _compile_interval_group_target(node)

            exercises.append(
                {
                    "exerciseType": 0,
                    "groupId": "0",
                    "id": group_id,
                    "intensityType": 0,
                    "intensityValue": 0,
                    "isGroup": True,
                    "name": "Interval",
                    "originId": "0",
                    "restType": 3,
                    "restValue": 0,
                    "sets": node.repeat,
                    "sortNo": group_sort,
                    "sportType": 1,
                    "targetType": group_target_type,
                    "targetValue": group_target_value,
                }
            )

            exercise_id += 1
            work_exercise, work_seconds = _base_exercise(
                node.work,
                exercise_id,
                _ACTION_EXERCISE_TYPES[node.work.action],
                group_sort + 65536,
                str(group_id),
            )
            exercises.append(work_exercise)

            exercise_id += 1
            recovery_exercise, recovery_seconds = _base_exercise(
                node.recovery,
                exercise_id,
                2,
                group_sort + 131072,
                str(group_id),
            )
            exercises.append(recovery_exercise)

            total_seconds += (work_seconds + recovery_seconds) * node.repeat
            continue

        exercise_id += 1
        exercise, duration_seconds = _base_exercise(
            node,
            exercise_id,
            _ACTION_EXERCISE_TYPES[node.action],
            group_sort,
            "0",
        )
        exercises.append(exercise)
        total_seconds += duration_seconds

    real_step_count = sum(1 for exercise in exercises if not exercise.get("isGroup"))

    return {
        "access": 1,
        "duration": total_seconds,
        "estimatedTime": total_seconds,
        "exerciseNum": real_step_count,
        "exercises": exercises,
        "gradeSystemVersion": 0,
        "hybridTotalSets": 0,
        "name": workout.name,
        "overview": workout.description,
        "poolLength": 0,
        "poolLengthId": 0,
        "poolLengthUnit": 0,
        "referExercise": {
            "gradeSystem": 0,
            "hrType": _refer_exercise_hr_type(workout),
            "intensityType": 0,
            "valueType": 1,
        },
        "sourceUrl": "",
        "sportType": 1,
        "subType": 65535,
        "totalSets": real_step_count,
        "trainingLoad": 0,
        "type": 0,
        "videoCoverUrl": "",
        "videoUrl": "",
    }
