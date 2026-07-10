from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

TargetType = Literal["distance", "time", "training_load", "open"]
IntensityType = Literal[
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
]
ActionType = Literal["warmup", "work", "recovery", "cooldown"]


@dataclass(slots=True)
class TargetSpec:
    type: TargetType
    value: float | int | None = None
    unit: str | None = None


@dataclass(slots=True)
class ZoneSpec:
    preset: str
    low: float | int | None = None
    high: float | int | None = None


@dataclass(slots=True)
class RangeSpec:
    low: float | int
    high: float | int | None = None


@dataclass(slots=True)
class IntensitySpec:
    type: IntensityType
    range: RangeSpec | None = None
    zone: ZoneSpec | None = None


@dataclass(slots=True)
class StepNode:
    kind: Literal["step"]
    action: ActionType
    target: TargetSpec
    intensity: IntensitySpec


@dataclass(slots=True)
class IntervalNode:
    kind: Literal["interval"]
    repeat: int
    work: StepNode
    recovery: StepNode


@dataclass(slots=True)
class RunningWorkout:
    name: str
    happen_day: str
    description: str = ""
    sort_no: int = 1
    steps: list[StepNode | IntervalNode] = field(default_factory=list)
