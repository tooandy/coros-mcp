from __future__ import annotations

from coros_mcp.running.models import IntervalNode, RunningWorkout


def _validate_step(step) -> None:
    if step.target.type == "open" and step.target.value is not None:
        raise ValueError("open target must not include value")
    if step.intensity.type == "none" and (step.intensity.range or step.intensity.zone):
        raise ValueError("none intensity must not include range or zone")
    if step.intensity.zone and step.intensity.zone.preset == "custom":
        if step.intensity.zone.low is None or step.intensity.zone.high is None:
            raise ValueError("custom zone requires both low and high values")


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
