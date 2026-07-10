from __future__ import annotations

from coros_mcp.running.models import IntervalNode, RunningWorkout
from coros_mcp.running.constraints import (
    is_direct_numeric_intensity,
    is_supported_target_unit,
    percent_zone_family_for,
    supported_target_units,
)

_ZONE_ALLOWED_INTENSITY_TYPES = {
    "heart_rate_percent_max",
    "heart_rate_percent_reserve",
    "heart_rate_percent_lthr",
    "pace_percent_lthr",
    "effort_pace_percent_threshold",
}


def _is_numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_step(step) -> None:
    if step.target.type == "open":
        if step.target.value is not None:
            raise ValueError("open target must not include value")
    else:
        if step.target.value is None:
            raise ValueError(f"{step.target.type} target requires value")
        if step.target.type == "training_load" and not _is_numeric(step.target.value):
            raise ValueError("training_load target requires numeric value")
        if step.target.type in {"distance", "time"} and not is_supported_target_unit(step.target.type, step.target.unit):
            allowed_units = ", ".join(supported_target_units(step.target.type))
            raise ValueError(f"{step.target.type} target requires supported unit: {allowed_units}")

    if step.intensity.type == "none" and (step.intensity.range or step.intensity.zone):
        raise ValueError("none intensity must not include range or zone")
    if step.intensity.range and step.intensity.zone:
        raise ValueError("intensity.range and intensity.zone are mutually exclusive")
    if step.intensity.type in _ZONE_ALLOWED_INTENSITY_TYPES and not step.intensity.range and not step.intensity.zone:
        raise ValueError("percent-based intensity types require range or zone")
    if is_direct_numeric_intensity(step.intensity.type):
        if step.intensity.zone:
            raise ValueError("zone is only supported for percent-based intensity types")
        if not step.intensity.range:
            raise ValueError(f"{step.intensity.type} intensity requires range")
        if step.intensity.range.low is None:
            raise ValueError(f"{step.intensity.type} intensity requires range.low")
        if not _is_numeric(step.intensity.range.low):
            raise ValueError(f"{step.intensity.type} intensity range.low must be numeric")
        if step.intensity.range.high is not None and not _is_numeric(step.intensity.range.high):
            raise ValueError(f"{step.intensity.type} intensity range.high must be numeric")
        return
    if step.intensity.zone and step.intensity.type not in _ZONE_ALLOWED_INTENSITY_TYPES:
        raise ValueError("zone is only supported for percent-based intensity types")
    if step.intensity.zone and step.intensity.zone.preset == "custom":
        if step.intensity.zone.low is None or step.intensity.zone.high is None:
            raise ValueError("custom zone requires both low and high values")
    if step.intensity.zone and step.intensity.zone.preset != "custom":
        zone_family = percent_zone_family_for(step.intensity.type)
        if zone_family is None:
            raise ValueError("zone is only supported for percent-based intensity types")
        if step.intensity.zone.preset not in zone_family:
            raise ValueError(
                f"zone preset '{step.intensity.zone.preset}' is invalid for intensity type '{step.intensity.type}'"
            )


def validate_running_workout(workout: RunningWorkout) -> None:
    if not workout.name:
        raise ValueError("name is required")
    if len(workout.happen_day) != 8 or not workout.happen_day.isdigit():
        raise ValueError("happen_day must be YYYYMMDD")
    if not workout.steps:
        raise ValueError("steps must be non-empty")

    for node in workout.steps:
        if isinstance(node, IntervalNode):
            if node.repeat < 1:
                raise ValueError("interval repeat must be >= 1")
            if node.work.action != "work":
                raise ValueError("interval work.action must be 'work'")
            if node.recovery.action != "recovery":
                raise ValueError("interval recovery.action must be 'recovery'")
            step_nodes = [node.work, node.recovery]
        else:
            step_nodes = [node]

        for step in step_nodes:
            _validate_step(step)
