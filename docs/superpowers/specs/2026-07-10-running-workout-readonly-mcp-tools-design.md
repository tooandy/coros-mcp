# Running Workout Read-Only MCP Tools Design

## Summary

This design adds a small running-first read-only MCP surface on top of the
existing semantic running domain layer in `coros-mcp`.

The goal is to make running workout authoring more agent-friendly before a
workout is actually scheduled. Instead of forcing an agent to jump straight to
`schedule_running_workout`, the MCP server should expose explicit tools for:

- normalization + validation
- human-readable rendering
- payload compilation
- combined preview

These tools are intentionally read-only:

- no network calls
- no auth requirement
- no calendar writes
- no library writes

They exist to close the authoring loop for MCP users and to prepare the code
shape for a later CLI without duplicating running logic.

## Problem

Today the running semantic model exists, but MCP callers only get one running
entry point:

- `schedule_running_workout`

That means an agent can only discover whether a running workout is valid by
trying to schedule it. This creates several problems:

- validation is not independently callable
- payload compilation is not inspectable
- rendering is not available without going through the scheduling tool
- preview-style workflows are awkward
- future CLI commands would have to expose concepts that MCP still hides

The problem is not missing running semantics in the domain layer. The problem is
that MCP does not yet expose those semantics as a read-only workflow.

## Goals

- Add running-first read-only MCP tools for validate, render, compile, and preview.
- Reuse the existing `normalize -> validate -> render -> compile` running domain flow.
- Keep scheduling behavior unchanged.
- Return structured result objects instead of surfacing raw exceptions to the MCP caller.
- Make `preview_running_workout` the preferred authoring/debugging entry point for agents.
- Keep the design directly reusable for future CLI commands.

## Non-Goals

- Changing the running semantic model itself
- Adding authentication to read-only running tools
- Scheduling or saving workouts from the new tools
- Replacing `schedule_running_workout`
- Implementing running template lifecycle in this phase
- Redesigning running rendering beyond what the current renderer already supports

## User-Facing MCP Changes

Add four new MCP tools:

### `validate_running_workout`

Purpose:

- normalize input
- validate semantic correctness
- return a structured success or failure result

Expected use:

- agent checks whether a workout shape is acceptable before scheduling
- human debugs invalid workout input

### `render_running_workout`

Purpose:

- normalize input
- validate it
- return the current human-readable summary string

Expected use:

- quick inspection by a user or agent
- downstream use by skills that want a concise textual preview

### `compile_running_workout`

Purpose:

- normalize input
- validate it
- compile the final COROS inline program payload

Expected use:

- compare semantic input with COROS wire output
- inspect mappings during reverse-engineering and QA

### `preview_running_workout`

Purpose:

- provide a one-shot read-only authoring result

It should return:

- normalized workout structure
- rendered summary
- compiled COROS payload
- validation success/failure state

Expected use:

- default tool for agent authoring flows
- “show me what would be scheduled” workflows

## Output Shape

All four tools should return structured dictionaries.

### Success shape

At minimum:

```json
{
  "ok": true
}
```

Each tool then adds its own tool-specific fields.

### Failure shape

All read-only tools should use a consistent failure contract:

```json
{
  "ok": false,
  "error": "human-readable error message"
}
```

No raw exception should escape the tool boundary.

## Proposed Tool Contracts

### `validate_running_workout`

Input:

- `name`
- `steps`
- `happen_day`
- `description` (optional)
- `sort_no` (optional)

Output on success:

```json
{
  "ok": true,
  "valid": true,
  "normalized_workout": { "...": "..." }
}
```

Output on failure:

```json
{
  "ok": false,
  "valid": false,
  "error": "..."
}
```

### `render_running_workout`

Input:

- same semantic running workout fields as above

Output on success:

```json
{
  "ok": true,
  "rendered_summary": "Warmup 15 min | 4 x [...]"
}
```

### `compile_running_workout`

Input:

- same semantic running workout fields as above

Output on success:

```json
{
  "ok": true,
  "program": { "...": "final coros payload ..." }
}
```

### `preview_running_workout`

Input:

- same semantic running workout fields as above

Output on success:

```json
{
  "ok": true,
  "valid": true,
  "normalized_workout": { "...": "..." },
  "rendered_summary": "...",
  "program": { "...": "..." }
}
```

## Design Constraints

### Reuse current domain logic

The new MCP tools must reuse the existing running modules:

- `normalize_running_workout`
- `validate_running_workout`
- `render_running_workout`
- `compile_running_workout`

The MCP layer should not add a second validation or compilation path.

### No auth requirement

Because these tools are read-only and purely local:

- they must not call `_get_auth()`
- they must not call `_run_with_auth()`
- they must not depend on stored COROS credentials

### Keep scheduling unchanged

`schedule_running_workout` remains the write path and is not replaced by these
tools.

## Implementation Shape

### Server layer

The implementation should stay inside `coros_mcp.server`.

Likely additions:

- a tiny shared helper that builds a `RunningWorkout` from MCP tool args
- a tiny shared helper that wraps exceptions into `{ok: false, error: ...}`

This avoids repeating the same normalize/validate boilerplate in four tools.

### Domain layer

The running domain layer should remain unchanged unless implementation reveals a
small gap in serialization convenience.

Expected outcome:

- no semantic behavior change
- only MCP exposure changes

## Serialization

`RunningWorkout`, `StepNode`, `IntervalNode`, and nested dataclasses are not
ideal raw MCP return values.

Therefore:

- success responses that include normalized structures should serialize them to
  plain dictionaries/lists
- this serialization should be deterministic and local to the running MCP path

The serialization only needs to support current running dataclasses and does not
need to become a generic framework.

## Testing

Add focused tests for:

- tool registration in `mcp.list_tools()`
- success and failure responses for `validate_running_workout`
- success and failure responses for `render_running_workout`
- success and failure responses for `compile_running_workout`
- success and failure responses for `preview_running_workout`
- confirmation that these tools do not require auth
- confirmation that scheduling behavior remains unchanged

Primary test location:

- `tests/test_running_tool.py`

If needed, small regression coverage may also land in:

- `tests/test_post_release_review_fixes.py`

## Documentation

Update `README.md` so the running tool surface is documented as:

- `preview_running_workout` for default authoring/debugging
- `validate_running_workout` for validation-only flows
- `render_running_workout` for summary-only flows
- `compile_running_workout` for payload inspection
- `schedule_running_workout` for actual calendar writes

This should make the tool selection story clearer for agents and humans.

## Risks

### Tool sprawl

Adding four tools increases the MCP surface area.

Mitigation:

- document the intended role of each tool clearly
- recommend `preview_running_workout` as the default read-only entry point

### Inconsistent result shapes

If each tool invents its own ad-hoc result format, agents will have a harder
time using them reliably.

Mitigation:

- use a shared `ok` / `error` contract
- keep field names stable and explicit

### Over-abstracting too early

This phase should not build a large generic framework around tool wrapping or
dataclass serialization.

Mitigation:

- keep helpers narrow
- only solve what the four running tools need

## Success Criteria

This design is successful when:

- MCP exposes four new read-only running tools
- the tools work without auth
- the tools return structured success/failure results
- they reuse existing running semantics instead of re-implementing them
- `schedule_running_workout` remains the only write path
- README clearly explains which running tool to use for which purpose

## Current Recommendation

Implement this read-only MCP layer before starting running template lifecycle
or CLI extraction.

That sequencing gives the project:

- a better MCP authoring loop now
- a clearer surface for agents
- a reusable shape for later CLI commands
