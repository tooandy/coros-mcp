from __future__ import annotations

from coros_mcp.running.models import IntervalNode, RunningWorkout, StepNode


def _format_target(step: StepNode) -> str:
    if step.target.type == "distance":
        return f"{int(step.target.value)} {step.target.unit}"
    if step.target.type == "time":
        return f"{int(step.target.value)} {step.target.unit}"
    if step.target.type == "training_load":
        return f"{int(step.target.value)} TL"
    return "open"


def _format_step(step: StepNode) -> str:
    return f"{step.action.capitalize()} {_format_target(step)}"


def render_running_workout(workout: RunningWorkout) -> str:
    parts: list[str] = []
    for node in workout.steps:
        if isinstance(node, IntervalNode):
            parts.append(f"{node.repeat} x [{_format_step(node.work)} / {_format_step(node.recovery)}]")
        else:
            parts.append(_format_step(node))
    return " | ".join(parts)
