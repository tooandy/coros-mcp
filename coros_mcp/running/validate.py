from __future__ import annotations

from coros_mcp.running.constraints import (
    is_direct_numeric_intensity,
    is_supported_target_unit,
    supported_target_units,
)
from coros_mcp.running.models import IntervalNode, RunningWorkout
from coros_mcp.running.zones import resolve_zone_range

_VALID_TARGET_TYPES = {"distance", "time", "training_load", "open"}
_VALID_INTENSITY_TYPES = {
    "heart_rate_percent_max",
    "heart_rate_percent_reserve",
    "heart_rate_percent_lthr",
    "heart_rate",
    "pace_percent_lthr",
    "pace",
    "effort_pace_percent_threshold",
    "effort_pace",
    "power",
    "cadence",
    "none",
}
_VALID_ACTIONS = {"warmup", "work", "recovery", "cooldown"}
_ZONE_ALLOWED_INTENSITY_TYPES = {
    "heart_rate_percent_max",
    "heart_rate_percent_reserve",
    "heart_rate_percent_lthr",
    "pace_percent_lthr",
    "effort_pace_percent_threshold",
}


def _is_numeric(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _validate_bounded_pair(low, high, label: str) -> None:
    if low is None or high is None:
        raise ValueError(f"{label} requires both low and high values")
    if not _is_numeric(low) or not _is_numeric(high):
        raise ValueError(f"{label} low/high must be numeric")
    if high < low:
        raise ValueError(f"{label} high must be >= low")


def _validate_direct_numeric_range(low, high, label: str) -> None:
    if low is None:
        raise ValueError(f"{label} requires both low and high values")
    if not _is_numeric(low):
        raise ValueError(f"{label} low/high must be numeric")
    if high is None:
        return
    if not _is_numeric(high):
        raise ValueError(f"{label} low/high must be numeric")
    if high < low:
        raise ValueError(f"{label} high must be >= low")


def _validate_step(step) -> None:
    if step.action not in _VALID_ACTIONS:
        raise ValueError(f"unsupported step action: {step.action!r}")
    if step.target.type not in _VALID_TARGET_TYPES:
        raise ValueError(f"unsupported target type: {step.target.type!r}")
    if step.intensity.type not in _VALID_INTENSITY_TYPES:
        raise ValueError(f"unsupported intensity type: {step.intensity.type!r}")
    if step.target.type == "training_load":
        raise ValueError("training_load target is not yet supported")

    if step.target.type == "open":
        if step.target.value is not None:
            raise ValueError("open target must not include value")
        if step.target.unit is not None:
            raise ValueError("open target must not include unit")
    else:
        if step.target.value is None:
            raise ValueError(f"{step.target.type} target requires value")
        if step.target.type in {"distance", "time"} and not _is_numeric(step.target.value):
            raise ValueError(f"{step.target.type} target requires numeric value")
        if step.target.type in {"distance", "time"} and not is_supported_target_unit(
            step.target.type, step.target.unit
        ):
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
        _validate_direct_numeric_range(
            step.intensity.range.low,
            step.intensity.range.high,
            f"{step.intensity.type} intensity range",
        )
        return
    if step.intensity.zone and step.intensity.type not in _ZONE_ALLOWED_INTENSITY_TYPES:
        raise ValueError("zone is only supported for percent-based intensity types")
    if step.intensity.zone and step.intensity.zone.preset == "custom":
        _validate_bounded_pair(step.intensity.zone.low, step.intensity.zone.high, "custom zone")
    if step.intensity.zone and step.intensity.zone.preset != "custom":
        resolve_zone_range(step.intensity.type, step.intensity.zone.preset)
    if step.intensity.range and step.intensity.type in _ZONE_ALLOWED_INTENSITY_TYPES:
        _validate_bounded_pair(step.intensity.range.low, step.intensity.range.high, "percent intensity range")


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
