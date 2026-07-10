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


def _normalize_intensity(payload: dict) -> IntensitySpec:
    range_payload = payload.get("range")
    zone_payload = payload.get("zone")
    return IntensitySpec(
        type=payload["type"],
        range=RangeSpec(**range_payload) if range_payload else None,
        zone=ZoneSpec(**zone_payload) if zone_payload else None,
    )


def _normalize_step(payload: dict) -> StepNode:
    return StepNode(
        kind="step",
        action=payload["action"],
        target=TargetSpec(**payload["target"]),
        intensity=_normalize_intensity(payload["intensity"]),
    )


def normalize_running_workout(payload: dict) -> RunningWorkout:
    steps: list[StepNode | IntervalNode] = []
    for step in payload["steps"]:
        if step["kind"] == "interval":
            steps.append(
                IntervalNode(
                    kind="interval",
                    repeat=int(step["repeat"]),
                    work=_normalize_step({"kind": "step", **step["work"]}),
                    recovery=_normalize_step({"kind": "step", **step["recovery"]}),
                )
            )
        else:
            steps.append(_normalize_step(step))

    return RunningWorkout(
        name=payload["name"],
        happen_day=payload["happen_day"],
        description=payload.get("description", ""),
        sort_no=int(payload.get("sort_no", 1)),
        steps=steps,
    )
