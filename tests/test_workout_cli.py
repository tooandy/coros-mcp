import json
from unittest.mock import patch

from coros_mcp import cli, coros_api


def _auth() -> coros_api.StoredAuth:
    return coros_api.StoredAuth(
        access_token="t",
        user_id="u",
        region="eu",
        timestamp=0,
        mobile_access_token=None,
        mobile_login_payload=None,
    )


def test_workout_cli_list_templates_outputs_all_templates(capsys, monkeypatch):
    async def fake_fetch_workout_templates(auth):
        return [{"id": "w-1", "name": "Workout"}]

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "fetch_workout_templates", fake_fetch_workout_templates)

    with patch.object(cli.sys, "argv", ["coros-mcp", "workout", "list-templates"]):
        result = cli.cmd_workout()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["count"] == 1
    assert output["workouts"][0]["id"] == "w-1"


def test_workout_cli_save_template_calls_api(capsys, monkeypatch):
    captured = {}
    payload = {
        "name": "Sweet Spot",
        "sport_type": 2,
        "intensity_type": 6,
        "steps": [
            {"name": "Warmup", "duration_minutes": 10, "intensity_low": 100, "intensity_high": 150},
            {"name": "Work", "duration_minutes": 20, "intensity_low": 250, "intensity_high": 275},
        ],
    }

    async def fake_save_workout_template(auth, name, steps, sport_type, intensity_type):
        captured["name"] = name
        captured["steps"] = steps
        captured["sport_type"] = sport_type
        captured["intensity_type"] = intensity_type
        return "template-42"

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "save_workout_template", fake_save_workout_template)

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "workout", "save-template", "--json", json.dumps(payload)],
    ):
        result = cli.cmd_workout()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["saved"] is True
    assert output["workout_id"] == "template-42"
    assert output["total_minutes"] == 30
    assert captured["sport_type"] == 2
    assert captured["intensity_type"] == 6


def test_workout_cli_schedule_template_calls_api(capsys, monkeypatch):
    captured = {}

    async def fake_schedule_workout_template(auth, workout_id, happen_day, sort_no):
        captured["workout_id"] = workout_id
        captured["happen_day"] = happen_day
        captured["sort_no"] = sort_no
        return {"id_in_plan": "42", "enrichment_ok": True}

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "schedule_workout_template", fake_schedule_workout_template)

    with patch.object(
        cli.sys,
        "argv",
        [
            "coros-mcp",
            "workout",
            "schedule-template",
            "--workout-id",
            "template-42",
            "--happen-day",
            "20260715",
            "--sort-no",
            "2",
        ],
    ):
        result = cli.cmd_workout()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["scheduled"] is True
    assert captured == {"workout_id": "template-42", "happen_day": "20260715", "sort_no": 2}


def test_workout_cli_delete_template_calls_api(capsys, monkeypatch):
    captured = {}

    async def fake_delete_workout_template(auth, workout_id):
        captured["workout_id"] = workout_id

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "delete_workout_template", fake_delete_workout_template)

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "workout", "delete-template", "--workout-id", "template-42"],
    ):
        result = cli.cmd_workout()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["deleted"] is True
    assert captured["workout_id"] == "template-42"
