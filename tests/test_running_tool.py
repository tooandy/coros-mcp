import asyncio

import pytest

from coros_mcp import coros_api
from coros_mcp.server import (
    compile_running_workout,
    list_running_workout_templates,
    mcp,
    preview_running_workout,
    render_running_workout,
    save_running_workout_template,
    schedule_running_workout_template,
    schedule_running_workout,
    validate_running_workout,
)


def _running_steps():
    return [
        {
            "kind": "step",
            "action": "warmup",
            "target": {"type": "time", "value": 15, "unit": "min"},
            "intensity": {"type": "none"},
        },
        {
            "kind": "interval",
            "repeat": 4,
            "work": {
                "action": "work",
                "target": {"type": "distance", "value": 1000, "unit": "m"},
                "intensity": {
                    "type": "pace_percent_lthr",
                    "zone": {"preset": "lactate_threshold_zone"},
                },
            },
            "recovery": {
                "action": "recovery",
                "target": {"type": "distance", "value": 400, "unit": "m"},
                "intensity": {"type": "none"},
            },
        },
    ]


def _invalid_running_steps():
    return [
        {
            "kind": "step",
            "action": "work",
            "target": {"type": "time", "value": 20, "unit": "min"},
            "intensity": {
                "type": "heart_rate_percent_max",
                "zone": {"preset": "aerobic_power_zone"},
            },
        }
    ]


def test_schedule_running_workout_is_registered():
    tools = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert "schedule_running_workout" in tools


def test_running_readonly_tools_are_registered():
    tools = {tool.name for tool in asyncio.run(mcp.list_tools())}

    assert "validate_running_workout" in tools
    assert "render_running_workout" in tools
    assert "compile_running_workout" in tools
    assert "preview_running_workout" in tools


def test_running_template_tools_are_registered():
    tools = {tool.name for tool in asyncio.run(mcp.list_tools())}

    assert "save_running_workout_template" in tools
    assert "list_running_workout_templates" in tools
    assert "schedule_running_workout_template" in tools


@pytest.mark.asyncio
async def test_validate_running_workout_returns_normalized_success_without_auth(monkeypatch):
    async def fail_get_auth():
        raise AssertionError("read-only running validation must not require auth")

    monkeypatch.setattr("coros_mcp.server._get_auth", fail_get_auth)

    result = await validate_running_workout(
        name="4x1km LT",
        description="Threshold repeats",
        happen_day="20260715",
        sort_no=3,
        steps=_running_steps(),
    )

    assert result["ok"] is True
    assert result["valid"] is True
    assert result["normalized_workout"]["name"] == "4x1km LT"
    assert result["normalized_workout"]["sort_no"] == 3
    assert result["normalized_workout"]["steps"][1]["kind"] == "interval"


@pytest.mark.asyncio
async def test_validate_running_workout_returns_structured_failure():
    result = await validate_running_workout(
        name="Broken",
        happen_day="20260715",
        steps=_invalid_running_steps(),
    )

    assert result["ok"] is False
    assert result["valid"] is False
    assert "error" in result
    assert "heart_rate_percent_max" in result["error"]


@pytest.mark.asyncio
async def test_render_running_workout_returns_summary_without_auth(monkeypatch):
    async def fail_get_auth():
        raise AssertionError("read-only running rendering must not require auth")

    monkeypatch.setattr("coros_mcp.server._get_auth", fail_get_auth)

    result = await render_running_workout(
        name="4x1km LT",
        description="Threshold repeats",
        happen_day="20260715",
        steps=_running_steps(),
    )

    assert result["ok"] is True
    assert "Warmup 15 min" in result["rendered_summary"]
    assert "4 x [" in result["rendered_summary"]


@pytest.mark.asyncio
async def test_render_running_workout_returns_structured_failure():
    result = await render_running_workout(
        name="Broken",
        happen_day="20260715",
        steps=_invalid_running_steps(),
    )

    assert result["ok"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_compile_running_workout_returns_program_without_auth(monkeypatch):
    async def fail_get_auth():
        raise AssertionError("read-only running compilation must not require auth")

    monkeypatch.setattr("coros_mcp.server._get_auth", fail_get_auth)

    result = await compile_running_workout(
        name="4x1km LT",
        description="Threshold repeats",
        happen_day="20260715",
        steps=_running_steps(),
    )

    assert result["ok"] is True
    assert result["program"]["overview"] == "Threshold repeats"
    assert result["program"]["exercises"][2]["targetType"] == 5
    assert result["program"]["exercises"][3]["exerciseType"] == 4


@pytest.mark.asyncio
async def test_compile_running_workout_returns_structured_failure():
    result = await compile_running_workout(
        name="Broken",
        happen_day="20260715",
        steps=_invalid_running_steps(),
    )

    assert result["ok"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_preview_running_workout_returns_full_readonly_result_without_auth(monkeypatch):
    async def fail_get_auth():
        raise AssertionError("read-only running preview must not require auth")

    monkeypatch.setattr("coros_mcp.server._get_auth", fail_get_auth)

    result = await preview_running_workout(
        name="4x1km LT",
        description="Threshold repeats",
        happen_day="20260715",
        sort_no=3,
        steps=_running_steps(),
    )

    assert result["ok"] is True
    assert result["valid"] is True
    assert result["normalized_workout"]["sort_no"] == 3
    assert "Warmup 15 min" in result["rendered_summary"]
    assert result["program"]["overview"] == "Threshold repeats"


@pytest.mark.asyncio
async def test_preview_running_workout_returns_structured_failure():
    result = await preview_running_workout(
        name="Broken",
        happen_day="20260715",
        steps=_invalid_running_steps(),
    )

    assert result["ok"] is False
    assert result["valid"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_schedule_running_workout_schedules_inline_and_renders_preview(monkeypatch):
    captured = {}

    async def fake_post_schedule_inline(auth, program, happen_day, sort_no):
        captured["auth"] = auth
        captured["program"] = program
        captured["happen_day"] = happen_day
        captured["sort_no"] = sort_no
        return {"id_in_plan": "42", "enrichment_ok": True}

    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_get_auth():
        return auth

    async def fake_run_with_auth(fn, auth, *args, **kwargs):
        return await fn(auth, *args)

    monkeypatch.setattr("coros_mcp.server._get_auth", fake_get_auth)
    monkeypatch.setattr("coros_mcp.server._run_with_auth", fake_run_with_auth)
    monkeypatch.setattr(coros_api, "_post_schedule_inline", fake_post_schedule_inline)

    result = await schedule_running_workout(
        name="4x1km LT",
        description="Threshold repeats",
        happen_day="20260715",
        sort_no=3,
        render_preview=True,
        steps=[
            {
                "kind": "step",
                "action": "warmup",
                "target": {"type": "time", "value": 15, "unit": "min"},
                "intensity": {"type": "none"},
            },
            {
                "kind": "interval",
                "repeat": 4,
                "work": {
                    "action": "work",
                    "target": {"type": "distance", "value": 1000, "unit": "m"},
                    "intensity": {
                        "type": "pace_percent_lthr",
                        "zone": {"preset": "lactate_threshold_zone"},
                    },
                },
                "recovery": {
                    "action": "recovery",
                    "target": {"type": "distance", "value": 400, "unit": "m"},
                    "intensity": {"type": "none"},
                },
            },
        ],
    )

    assert captured["program"]["overview"] == "Threshold repeats"
    assert captured["happen_day"] == "20260715"
    assert captured["sort_no"] == 3
    assert result["scheduled"] is True
    assert result["steps_count"] == 4
    assert "Warmup 15 min" in result["rendered_summary"]


@pytest.mark.asyncio
async def test_schedule_running_workout_returns_error_payload_on_invalid_input(monkeypatch):
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_get_auth():
        return auth

    monkeypatch.setattr("coros_mcp.server._get_auth", fake_get_auth)

    result = await schedule_running_workout(
        name="Broken",
        description="Bad zone family",
        happen_day="20260715",
        strict=True,
        steps=[
            {
                "kind": "step",
                "action": "work",
                "target": {"type": "time", "value": 20, "unit": "min"},
                "intensity": {
                    "type": "heart_rate_percent_max",
                    "zone": {"preset": "aerobic_power_zone"},
                },
            }
        ],
    )

    assert result["scheduled"] is False
    assert "error" in result


@pytest.mark.asyncio
async def test_list_running_workout_templates_filters_to_running(monkeypatch):
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_get_auth():
        return auth

    async def fake_run_with_auth(fn, auth, *args, **kwargs):
        assert fn is coros_api.fetch_workout_templates
        return [
            {"id": "run-1", "name": "Run", "sport_type": 1},
            {"id": "bike-1", "name": "Bike", "sport_type": 2},
        ]

    monkeypatch.setattr("coros_mcp.server._get_auth", fake_get_auth)
    monkeypatch.setattr("coros_mcp.server._run_with_auth", fake_run_with_auth)

    result = await list_running_workout_templates()

    assert result["count"] == 1
    assert result["workouts"] == [{"id": "run-1", "name": "Run", "sport_type": 1}]


@pytest.mark.asyncio
async def test_save_running_workout_template_saves_compiled_program(monkeypatch):
    captured = {}
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_get_auth():
        return auth

    async def fake_save_workout_program(auth, program):
        captured["program"] = program
        return "template-42"

    async def fake_run_with_auth(fn, auth, *args, **kwargs):
        return await fn(auth, *args)

    monkeypatch.setattr("coros_mcp.server._get_auth", fake_get_auth)
    monkeypatch.setattr("coros_mcp.server._run_with_auth", fake_run_with_auth)
    monkeypatch.setattr(coros_api, "save_workout_program", fake_save_workout_program)

    result = await save_running_workout_template(
        name="4x1km LT Template",
        description="Reusable LT repeats",
        render_preview=True,
        steps=_running_steps(),
    )

    assert result["saved"] is True
    assert result["workout_id"] == "template-42"
    assert result["steps_count"] == 4
    assert captured["program"]["sportType"] == 1
    assert captured["program"]["name"] == "4x1km LT Template"
    assert captured["program"]["overview"] == "Reusable LT repeats"
    assert "Warmup 15 min" in result["rendered_summary"]


@pytest.mark.asyncio
async def test_schedule_running_workout_template_checks_template_is_running(monkeypatch):
    captured = {}
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_get_auth():
        return auth

    async def fake_fetch_workout_templates(auth):
        return [
            {"id": "run-1", "name": "Run Template", "sport_type": 1},
            {"id": "bike-1", "name": "Bike Template", "sport_type": 2},
        ]

    async def fake_schedule_workout_template(auth, workout_id, happen_day, sort_no):
        captured["workout_id"] = workout_id
        captured["happen_day"] = happen_day
        captured["sort_no"] = sort_no
        return {"id_in_plan": "42", "enrichment_ok": True}

    async def fake_run_with_auth(fn, auth, *args, **kwargs):
        return await fn(auth, *args)

    monkeypatch.setattr("coros_mcp.server._get_auth", fake_get_auth)
    monkeypatch.setattr("coros_mcp.server._run_with_auth", fake_run_with_auth)
    monkeypatch.setattr(coros_api, "fetch_workout_templates", fake_fetch_workout_templates)
    monkeypatch.setattr(coros_api, "schedule_workout_template", fake_schedule_workout_template)

    result = await schedule_running_workout_template("run-1", "20260715", sort_no=3)

    assert result["scheduled"] is True
    assert result["name"] == "Run Template"
    assert captured == {"workout_id": "run-1", "happen_day": "20260715", "sort_no": 3}

    non_running = await schedule_running_workout_template("bike-1", "20260715")

    assert non_running["scheduled"] is False
    assert "not found" in non_running["error"]
