from __future__ import annotations

from coros_mcp.running.models import (
    IntensitySpec,
    IntervalNode,
    RangeSpec,
    RunningWorkout,
    StepNode,
    TargetSpec,
    ZoneSpec,
)


def _normalize_interval_repeat(value) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"interval repeat must be an integer, got {value!r}")
    return value


def _normalize_intensity(payload: dict) -> IntensitySpec:
    range_payload = payload.get("range")
    zone_payload = payload.get("zone")
    return IntensitySpec(
        type=payload["type"],
        range=RangeSpec(**range_payload) if range_payload else None,
        zone=ZoneSpec(**zone_payload) if zone_payload else None,
    )


def _normalize_step(payload: dict) -> StepNode:
    kind = payload.get("kind", "step")
    if kind != "step":
        raise ValueError(f"unsupported step kind: {kind!r}")
    return StepNode(
        kind="step",
        action=payload["action"],
        target=TargetSpec(**payload["target"]),
        intensity=_normalize_intensity(payload["intensity"]),
    )


def normalize_running_workout(payload: dict) -> RunningWorkout:
    steps: list[StepNode | IntervalNode] = []
    for step in payload["steps"]:
        kind = step.get("kind", "step")
        if kind == "interval":
            steps.append(
                IntervalNode(
                    kind="interval",
                    repeat=_normalize_interval_repeat(step["repeat"]),
                    work=_normalize_step(step["work"]),
                    recovery=_normalize_step(step["recovery"]),
                )
            )
        elif kind == "step":
            steps.append(_normalize_step(step))
        else:
            raise ValueError(f"unsupported step kind: {kind!r}")

    return RunningWorkout(
        name=payload["name"],
        happen_day=payload["happen_day"],
        description=payload.get("description", ""),
        sort_no=int(payload.get("sort_no", 1)),
        steps=steps,
    )
