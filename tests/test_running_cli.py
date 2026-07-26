import json
from unittest.mock import patch

from coros_mcp import cli, coros_api


def _payload() -> dict:
    return {
        "name": "4x1km LT",
        "description": "Threshold repeats",
        "happen_day": "20260715",
        "steps": [
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
    }


def test_running_cli_preview_outputs_render_and_program(capsys):
    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "running", "preview", "--json", json.dumps(_payload())],
    ):
        result = cli.cmd_running()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert result == 0
    assert payload["ok"] is True
    assert payload["valid"] is True
    assert "Warmup 15 min" in payload["rendered_summary"]
    assert payload["program"]["sportType"] == 1


def test_running_cli_validate_returns_failure_payload(capsys):
    invalid = {
        "name": "Broken",
        "happen_day": "20260715",
        "steps": [
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
    }

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "running", "validate", "--json", json.dumps(invalid)],
    ):
        result = cli.cmd_running()

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert result == 1
    assert payload["ok"] is False
    assert payload["valid"] is False
    assert "heart_rate_percent_max" in payload["error"]


def test_cli_help_lists_running_command(capsys):
    result = cli.cmd_help()

    captured = capsys.readouterr()

    assert result == 0
    assert "coros-mcp running ACTION" in captured.out


def test_running_cli_schedule_posts_compiled_program(capsys, monkeypatch):
    captured = {}
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_post_schedule_inline(auth, program, happen_day, sort_no):
        captured["program"] = program
        captured["happen_day"] = happen_day
        captured["sort_no"] = sort_no
        return {"id_in_plan": "42", "enrichment_ok": True}

    monkeypatch.setattr(cli, "get_stored_auth", lambda: auth)
    monkeypatch.setattr(coros_api, "_post_schedule_inline", fake_post_schedule_inline)

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "running", "schedule", "--json", json.dumps(_payload()), "--render-preview"],
    ):
        result = cli.cmd_running()

    payload = json.loads(capsys.readouterr().out)

    assert result == 0
    assert payload["scheduled"] is True
    assert payload["happen_day"] == "20260715"
    assert captured["program"]["sportType"] == 1
    assert captured["sort_no"] == 1
    assert "Warmup 15 min" in payload["rendered_summary"]


def test_running_cli_save_template_uses_placeholder_date(capsys, monkeypatch):
    captured = {}
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )
    payload = _payload()
    payload.pop("happen_day")

    async def fake_save_workout_program(auth, program):
        captured["program"] = program
        return "template-42"

    monkeypatch.setattr(cli, "get_stored_auth", lambda: auth)
    monkeypatch.setattr(coros_api, "save_workout_program", fake_save_workout_program)

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "running", "save-template", "--json", json.dumps(payload)],
    ):
        result = cli.cmd_running()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["saved"] is True
    assert output["workout_id"] == "template-42"
    assert captured["program"]["name"] == "4x1km LT"


def test_running_cli_list_templates_filters_to_running(capsys, monkeypatch):
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_fetch_workout_templates(auth):
        return [
            {"id": "run-1", "name": "Run", "sport_type": 1},
            {"id": "bike-1", "name": "Bike", "sport_type": 2},
        ]

    monkeypatch.setattr(cli, "get_stored_auth", lambda: auth)
    monkeypatch.setattr(coros_api, "fetch_workout_templates", fake_fetch_workout_templates)

    with patch.object(cli.sys, "argv", ["coros-mcp", "running", "list-templates"]):
        result = cli.cmd_running()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["count"] == 1
    assert output["workouts"][0]["id"] == "run-1"


def test_running_cli_schedule_template_rejects_non_running_template(capsys, monkeypatch):
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_fetch_workout_templates(auth):
        return [{"id": "bike-1", "name": "Bike", "sport_type": 2}]

    monkeypatch.setattr(cli, "get_stored_auth", lambda: auth)
    monkeypatch.setattr(coros_api, "fetch_workout_templates", fake_fetch_workout_templates)

    with patch.object(
        cli.sys,
        "argv",
        [
            "coros-mcp",
            "running",
            "schedule-template",
            "--workout-id",
            "bike-1",
            "--happen-day",
            "20260715",
        ],
    ):
        result = cli.cmd_running()

    output = json.loads(capsys.readouterr().out)

    assert result == 1
    assert output["ok"] is False
    assert "not found" in output["error"]


def test_running_cli_delete_template_checks_template_is_running(capsys, monkeypatch):
    captured = {}
    auth = coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )

    async def fake_fetch_workout_templates(auth):
        return [{"id": "run-1", "name": "Run Template", "sport_type": 1}]

    async def fake_delete_workout_template(auth, workout_id):
        captured["workout_id"] = workout_id

    monkeypatch.setattr(cli, "get_stored_auth", lambda: auth)
    monkeypatch.setattr(coros_api, "fetch_workout_templates", fake_fetch_workout_templates)
    monkeypatch.setattr(coros_api, "delete_workout_template", fake_delete_workout_template)

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "running", "delete-template", "--workout-id", "run-1"],
    ):
        result = cli.cmd_running()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["deleted"] is True
    assert output["name"] == "Run Template"
    assert captured["workout_id"] == "run-1"
