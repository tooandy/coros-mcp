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

## Review Fixes

Addressed the three review findings without broadening scope:

- `normalize_running_workout()` now raises `ValueError` for any unsupported `kind` instead of falling back to `step`.
- `validate_running_workout()` now rejects `zone` on non-percent intensity types.
- `validate_running_workout()` now rejects `intensity.range` and `intensity.zone` when both are present.

### Additional Regression Coverage

Added tests to cover:

- unknown `kind` is rejected during normalization
- absolute intensity types cannot carry `zone`
- `range` and `zone` are mutually exclusive

### Verification

Ran the task-specific test file after the fix:

```bash
cd /Users/aniss/Documents/Marathon/coros-mcp && .venv/bin/pytest tests/test_running_models.py -v
```

Result: 6 passed

## Review Fixes Round 2

Addressed the two remaining review findings without expanding scope:

- `validate_running_workout()` now rejects percent-based intensity types when both `range` and `zone` are absent.
- `validate_running_workout()` now rejects missing `value` for non-`open` targets.
- `validate_running_workout()` now rejects missing `unit` for `distance` and `time` targets.
- `validate_running_workout()` now requires a numeric `value` for `training_load` targets.

### Additional Regression Coverage

Added tests to cover:

- percent-based intensity types without `range` or `zone`
- missing required `value` / `unit` fields on non-`open` targets

### Verification

Ran the task-specific test file after the second fix:

```bash
cd /Users/aniss/Documents/Marathon/coros-mcp && .venv/bin/pytest tests/test_running_models.py -q
```

Result: 12 passed

## Review Fixes Round 3

Addressed the final four review findings without expanding scope:

- `training_load` targets now require a numeric `value`; string-like values are rejected.
- Direct numeric intensity types (`heart_rate`, `pace`, `power`, `cadence`, `effort_pace`) now require `range`, and `range.low` must be present and numeric.
- `distance` and `time` targets now validate `unit` against the current supported set instead of accepting any non-empty string.
- `%`-based intensity presets now validate against the correct family for each intensity type; invalid presets and mismatched families are rejected.

### Additional Regression Coverage

Added tests to cover:

- non-numeric `training_load.value`
- direct numeric intensity without `range`
- direct numeric intensity with `range.low = null`
- unsupported `distance` and `time` units
- invalid percent intensity presets and family mismatches

### Verification

Ran the task-specific test file after the final hardening pass:

```bash
cd /Users/aniss/Documents/Marathon/coros-mcp && .venv/bin/pytest tests/test_running_models.py -v
```

Result: 20 passed

## Review Fixes Round 4

Addressed the last two review findings without broadening scope:

- `distance` and `time` targets now require numeric `value`; string-like values are rejected.
- `%`-based intensity `range.low/high` and `zone.preset=custom` `low/high` now require numeric bounds, and invalid bound ordering is rejected.

### Additional Regression Coverage

Added tests to cover:

- non-numeric `distance` / `time` target values
- non-numeric `%` intensity `range.low`
- non-numeric `custom` zone `high`
- reversed `custom` zone bounds where `high < low`

### Verification

Ran the task-specific test file after the fix:

```bash
cd /Users/aniss/Documents/Marathon/coros-mcp && .venv/bin/pytest tests/test_running_models.py -v
```

Result: 25 passed
