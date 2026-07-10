# COROS MCP Running Workout Enhancement Design

## Summary

This design enhances `coros-mcp`'s running workout scheduling without pausing to build a separate CLI first.
The goal is to make running workouts understandable and reliable for LLMs and agents while preserving current MCP behavior.

We will:

- add a new MCP tool: `schedule_running_workout`
- keep `schedule_workout` for backward compatibility
- introduce a reusable running-workout semantic model inside the core library
- compile that semantic model into the COROS payload format required by `/training/schedule/update`
- leave the door open for a future CLI by keeping semantic parsing, normalization, validation, rendering, and payload compilation outside the MCP tool layer

This design focuses on a single running workout scheduled on a single day.
It does not yet cover weekly plans, multi-workout day orchestration, or Training Plan authoring.

## Problem

Current running workout support is not expressive enough for the COROS product model.

Today, the implementation mainly supports:

- flat or repeat-group steps
- time-based step duration
- sparse intensity values (`intensity_low` / `intensity_high`)
- running metadata needed to keep the payload renderable in COROS

It does not explicitly model:

- action types: warmup, work, recovery, cooldown, interval
- target types: distance, time, training load, open
- the full running intensity taxonomy
- intensity presets vs custom percentage ranges
- a running-first input shape that an agent can reason about directly

## Goals

- Provide an MCP-native, agent-friendly tool for scheduling running workouts.
- Model COROS running concepts explicitly instead of forcing LLMs to infer them from low-level fields.
- Support intensity ranges, not only single values.
- Support both preset zones and custom percentage ranges for `%`-based intensity types.
- Preserve existing `schedule_workout` behavior for non-running and legacy callers.
- Isolate reusable logic so the same internals can later power a CLI.

## Non-Goals

- Replacing MCP with a CLI in this phase
- Full Training Plan create/edit flows
- Weekly microcycle authoring
- Natural-language parsing in core code
- Strength and cycling DSL redesign

## User-Facing MCP Changes

### New Tool

Add `schedule_running_workout`.

This tool becomes the preferred entry point for new running-workout scheduling flows.
It accepts a semantic running-workout schema instead of the current generic `steps` contract.

### Existing Tool

Keep `schedule_workout`.

Compatibility strategy:

- no breaking changes for existing callers
- non-running usage keeps the current path
- running callers may continue using the legacy input
- future running enhancements inside `schedule_workout` should reuse the same semantic compiler where practical

## Semantic Model

The new model has two node kinds:

- `step`: a normal running step
- `interval`: a repeated container with `work` and `recovery`

### Running Workout Shape

```yaml
name: "4x1km LT"
description: "Lactate-threshold session"
happen_day: "20260715"
sort_no: 1

steps:
  - kind: step
    action: warmup
    target:
      type: time
      value: 15
      unit: min
    intensity:
      type: heart_rate_percent_max
      zone:
        preset: warmup_zone

  - kind: interval
    repeat: 4
    work:
      action: work
      target:
        type: distance
        value: 1000
        unit: m
      intensity:
        type: pace_percent_lthr
        zone:
          preset: lactate_threshold_zone
    recovery:
      action: recovery
      target:
        type: distance
        value: 400
        unit: m
      intensity:
        type: none

  - kind: step
    action: cooldown
    target:
      type: time
      value: 10
      unit: min
    intensity:
      type: none
```

## Domain Enums

### Action Types

- `warmup`
- `work`
- `recovery`
- `cooldown`

`interval` is not an action type.
It is a structural node that contains one `work` step and one `recovery` step.

### Target Types

- `distance`
- `time`
- `training_load`
- `open`

Preferred public shape:

```yaml
target:
  type: distance
  value: 1000
  unit: m
```

Compatibility aliases may be accepted later, but the core model should normalize everything into this structure.

### Intensity Types

The semantic model must support these running intensity types:

- `heart_rate_percent_max`
- `heart_rate_percent_reserve`
- `heart_rate_percent_lthr`
- `heart_rate`
- `pace_percent_lthr`
- `pace`
- `effort_pace_percent_threshold`
- `effort_pace`
- `power`
- `cadence`
- `none`

## Intensity Model

Intensity must support ranges.
A single scalar `value` is not sufficient.

### Direct Numeric Intensities

Examples: heart rate, pace, power, cadence.

```yaml
intensity:
  type: heart_rate
  range:
    low: 165
    high: 172
```

```yaml
intensity:
  type: pace
  range:
    low: 240000
    high: 250000
```

### Percentage-Based Intensities

These intensities support preset zones and custom percentage ranges.

Preset form:

```yaml
intensity:
  type: pace_percent_lthr
  zone:
    preset: lactate_threshold_zone
```

Custom form:

```yaml
intensity:
  type: pace_percent_lthr
  zone:
    preset: custom
    low: 95
    high: 98
```

The semantic layer stores the user's business intent.
The compiler layer resolves preset names into concrete percentage ranges.

## Zone Preset Families

Two preset families are needed.

### `% Max HR`

- `recovery_zone`
- `warmup_zone`
- `fat_burn_zone`
- `aerobic_endurance_zone`
- `lactate_threshold_zone`
- `anaerobic_zone`
- `custom`

### `% Reserve HR`, `% LTHR`, `% LTH Pace`, `% Effort Threshold Pace`

- `active_recovery_zone`
- `aerobic_endurance_zone`
- `aerobic_power_zone`
- `lactate_threshold_zone`
- `speed_endurance_zone`
- `anaerobic_power_zone`
- `custom`

The exact low/high boundaries should not be hardcoded into the MCP tool layer.
They belong in a zone mapping table in the reusable running domain module.

## Internal Architecture

Add a reusable running domain layer under `coros_mcp`.

Suggested module split:

- `coros_mcp/running/models.py`
  - semantic dataclasses or Pydantic-like structures
  - enums
  - normalized internal types
- `coros_mcp/running/normalize.py`
  - shape normalization
  - defaulting
  - preset resolution
- `coros_mcp/running/validate.py`
  - semantic validation rules
- `coros_mcp/running/compile.py`
  - COROS payload compilation
- `coros_mcp/running/render.py`
  - human-readable workout summary for debugging and future CLI reuse

The MCP server should call this layer, not embed running business logic directly in `server.py`.

## Compilation Strategy

The compiler converts the semantic running model into the payload shape consumed by the existing scheduling path.

### General Rules

- `warmup`, `work`, `recovery`, `cooldown` compile into concrete exercise rows
- `interval` compiles into one group row plus two sub-steps
- all running payloads still pass through the existing running metadata requirements
- `sport_type` remains running-side activity namespace externally and COROS wire namespace internally

### Action Mapping

Compiler should map actions to COROS `exerciseType` explicitly:

- `warmup` -> `1`
- `work` -> `2`
- `recovery` -> `4` if COROS accepts and renders it correctly for running; otherwise `2` plus recovery-specific metadata
- `cooldown` -> `3`

This point requires validation against live COROS behavior because current code only uses `1/2/3`.
The semantic model must still preserve `recovery` distinctly even if the wire mapping initially falls back to `2`.

### Target Mapping

Compiler must support:

- `time` -> running target time fields
- `distance` -> running target distance fields
- `training_load` -> training load target if supported by the wire payload
- `open` -> no explicit target

If COROS does not support one of these cleanly in the current running workout endpoint, validation must fail with an actionable error instead of silently degrading semantics.

### Intensity Mapping

Compiler must map semantic intensity types into COROS fields such as:

- `intensityType`
- `intensityValue`
- `intensityValueExtend`
- `intensityMultiplier`
- `intensityDisplayUnit`
- `hrType`
- `targetDisplayUnit`
- any percentage-related fields COROS requires

Mapping logic must preserve low/high ranges.

## Validation Rules

Validation should happen before payload compilation.

### Workout-Level

- `name` required
- `happen_day` required and must be `YYYYMMDD`
- `steps` must be non-empty

### Step-Level

- `kind` must be `step` or `interval`
- `action` required for normal steps
- `target` required unless `target.type == open`
- `intensity.type` required

### Interval-Level

- `repeat >= 1`
- `work` required
- `recovery` required
- `work.action` must normalize to `work`
- `recovery.action` must normalize to `recovery`

### Target-Level

- `distance` requires a supported unit, initially `m`
- `time` requires a supported unit, initially `min` or `sec`
- `training_load` requires numeric value
- `open` must not include `value`

### Intensity-Level

- direct numeric intensities require `range.low`
- `range.high` optional only if COROS truly supports open-ended high bounds for that intensity type
- preset zones must belong to a valid preset family for that intensity type
- `preset=custom` requires both `low` and `high`
- `none` must not carry a range or zone

## MCP Tool Contract

### `schedule_running_workout`

Inputs:

- `name: str`
- `happen_day: str`
- `steps: list[dict]`
- `description: str = ""`
- `sort_no: int = 1`

Optional future-friendly flags:

- `render_preview: bool = False`
- `strict: bool = True`

Response shape should follow the current scheduling family:

- `scheduled: bool`
- `name: str`
- `happen_day: str`
- `steps_count: int`
- `response: dict`
- optional `warning`
- optional `rendered_summary`

## Compatibility and Migration

### For Existing Callers

- no behavior changes for existing non-running `schedule_workout` calls
- existing running `schedule_workout` calls continue to work

### For New Running Callers

- prefer `schedule_running_workout`
- document it as the recommended tool for new running flows

### Internal Migration

Phase 1:

- add the new tool
- add reusable running semantic internals
- do not modify legacy generic builder except where shared helpers are extracted

Phase 2:

- optionally allow `schedule_workout` with `sport_type in {100,102,103}` to delegate into the new compiler when callers provide the new semantic running shape

## Testing Strategy

Add unit tests for:

- schema normalization
- zone preset resolution
- range validation
- interval compilation
- target mapping
- intensity mapping
- compatibility with existing running metadata

Add regression tests for:

- current legacy `schedule_workout` running calls still succeed
- `schedule_running_workout` emits removable scheduled entries
- description still maps to `overview`
- running distance targets stay metric in display fields

## Risks

### Unknown COROS Wire Semantics

Some user-visible COROS concepts may not map 1:1 to currently implemented wire fields.
Examples include:

- explicit recovery action type
- training-load target steps
- some percentage-based intensity modes

Mitigation:

- keep semantic model richer than current compiler
- fail explicitly on unsupported mappings
- add mapping incrementally as payload evidence is collected

### Tool Overlap

Two similar tools can confuse agents.

Mitigation:

- clearly document `schedule_running_workout` as preferred for running
- clearly document `schedule_workout` as generic/legacy

## Rollout Plan

1. Introduce running semantic internals and tests.
2. Add `schedule_running_workout`.
3. Document the new tool in `README.md`.
4. Add examples for common running workouts.
5. Optionally teach `schedule_workout` to reuse the same internals for enriched running inputs.

## Future CLI Path

This design intentionally keeps normalization, validation, compilation, and rendering outside the MCP tool layer.
That allows a future CLI to expose commands like:

- `coros running validate`
- `coros running compile`
- `coros running render`
- `coros running schedule`

without re-implementing running workout logic.
