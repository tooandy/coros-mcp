import asyncio

import pytest

from coros_mcp import coros_api
from coros_mcp.server import mcp, schedule_running_workout


def test_schedule_running_workout_is_registered():
    tools = {tool.name for tool in asyncio.run(mcp.list_tools())}
    assert "schedule_running_workout" in tools


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
