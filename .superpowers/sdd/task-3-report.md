# Task 3 Report: Compile Semantic Running Workouts Into COROS Programs

## Status

DONE

## Brief Scope

- Read and implemented only the Task 3 brief in `.superpowers/sdd/task-3-brief.md`.
- Stayed within the requested file boundary:
  - Created `coros_mcp/running/compile.py`
  - Modified `coros_mcp/running/__init__.py`
  - Added `tests/test_running_compile.py`
- Did not add any MCP tool surface.

## Existing Workspace Context

- Detected unrelated untracked files in `.superpowers/sdd/` and `docs/`.
- Did not revert or modify those parallel changes.

## TDD Evidence

### Red

Added `tests/test_running_compile.py` first, then ran:

```bash
./.venv/bin/pytest tests/test_running_compile.py -v
```

Observed expected failure during collection:

- `ModuleNotFoundError: No module named 'coros_mcp.running.compile'`

### Green

Implemented the minimal compiler and package export, then reran:

```bash
./.venv/bin/pytest tests/test_running_compile.py -v
```

Observed:

- `3 passed`

## What Was Implemented

### `coros_mcp.running.compile.compile_running_workout`

Implemented a compiler that:

- Re-validates incoming `RunningWorkout` via `validate_running_workout`
- Compiles top-level steps and interval groups into COROS `program` payload rows
- Emits running wire metadata at the program level:
  - `sportType=1`
  - `subType=65535`
  - `referExercise`
  - duration / estimatedTime / exerciseNum / totalSets
- Maps running actions to COROS `exerciseType`
  - `warmup -> 1`
  - `work -> 2`
  - `recovery -> 4`
  - `cooldown -> 3`
- Compiles targets:
  - `time` -> COROS target type 2, seconds
  - `distance` -> COROS target type 5, centi-meters wire value + metric display unit
  - `open` -> COROS target type 0
- Compiles supported intensities:
  - `none`
  - heart-rate percent families
  - direct `heart_rate`
  - `pace_percent_lthr`
  - direct `pace`
  - direct `power`
  - direct `cadence`
- Resolves zone presets through `resolve_zone_range`
- Accumulates duration only from time-based steps, including repeated interval sub-steps when they are time-targeted

## Explicit Failure Decisions

Per the brief requirement to fail explicitly instead of silently degrading:

- `training_load` targets raise `ValueError`
- `effort_pace`
- `effort_pace_percent_threshold`

These effort-pace semantics are currently validated by Task 1/2 but are not compiled here because the correct COROS wire encoding is not established in the existing codebase. Failing loudly is safer than downgrading them into pace/speed/cadence semantics.

## Tests Added

- `test_compile_running_workout_builds_group_and_overview`
- `test_compile_running_workout_rejects_training_load_until_supported`
- `test_compile_running_workout_rejects_unsupported_effort_pace_semantics`

## Verification Run

Final verification command run before commit:

```bash
./.venv/bin/pytest tests/test_running_compile.py -v
```

Result:

- `3 passed in 0.01s`

## Concerns

- `effort_pace` and `effort_pace_percent_threshold` remain intentionally unsupported in compilation.
- Interval group header target currently mirrors the interval work target, which matches the brief’s minimal shape but may need revisiting in a later task if COROS group rows need richer semantics for distance/open mixes.
