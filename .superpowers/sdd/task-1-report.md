# Task 1 Report

## Goal

Add an independent running workout semantic layer under `coros_mcp.running` for model/normalize/validate only, while leaving existing `schedule_workout` behavior unchanged.

## Implemented

- Added `coros_mcp.running.models` with:
  - `TargetSpec`
  - `IntensitySpec`
  - `StepNode`
  - `IntervalNode`
  - `RunningWorkout`
- Added `coros_mcp.running.normalize.normalize_running_workout(payload: dict) -> RunningWorkout`
- Added `coros_mcp.running.validate.validate_running_workout(workout: RunningWorkout) -> None`
- Added `coros_mcp.running.__init__` exports for the new semantic layer
- Added `tests/test_running_models.py` covering:
  - step and interval normalization
  - custom zone validation
  - open target validation

## Validation

Ran only the task-specific test file:

```bash
cd /Users/aniss/Documents/Marathon/coros-mcp && .venv/bin/pytest tests/test_running_models.py -v
```

Result: 3 passed

## Notes

- The new code is isolated under `coros_mcp.running` and does not touch existing workout scheduling code paths.
- I did not run the full test suite, per task instructions.
