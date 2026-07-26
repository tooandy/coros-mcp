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


def _payload() -> dict:
    return {
        "name": "Leg Circuit",
        "happen_day": "20260715",
        "sets": 2,
        "exercises": [
            {
                "origin_id": "54",
                "name": "T1061",
                "overview": "sid_strength_squats",
                "target_type": 3,
                "target_value": 12,
                "rest_seconds": 45,
            }
        ],
    }


def test_strength_cli_list_exercises_outputs_catalog(capsys, monkeypatch):
    async def fake_fetch_exercises(auth, sport_type):
        return [{"id": "54", "name": "T1061"}]

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "fetch_exercises", fake_fetch_exercises)

    with patch.object(cli.sys, "argv", ["coros-mcp", "strength", "list-exercises"]):
        result = cli.cmd_strength()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["count"] == 1
    assert output["sport_type"] == 4


def test_strength_cli_save_template_calls_api(capsys, monkeypatch):
    captured = {}

    async def fake_save_strength_workout_template(auth, name, exercises, sets):
        captured["name"] = name
        captured["exercises"] = exercises
        captured["sets"] = sets
        return "strength-42"

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "save_strength_workout_template", fake_save_strength_workout_template)

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "strength", "save-template", "--json", json.dumps(_payload())],
    ):
        result = cli.cmd_strength()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["saved"] is True
    assert output["workout_id"] == "strength-42"
    assert captured["sets"] == 2


def test_strength_cli_schedule_calls_api(capsys, monkeypatch):
    captured = {}

    async def fake_schedule_strength_workout(auth, name, exercises, happen_day, sets, sort_no):
        captured["name"] = name
        captured["happen_day"] = happen_day
        captured["sets"] = sets
        captured["sort_no"] = sort_no
        return {"id_in_plan": "42", "enrichment_ok": True}

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "schedule_strength_workout", fake_schedule_strength_workout)

    with patch.object(
        cli.sys,
        "argv",
        [
            "coros-mcp",
            "strength",
            "schedule",
            "--json",
            json.dumps(_payload()),
            "--happen-day",
            "20260716",
            "--sort-no",
            "3",
        ],
    ):
        result = cli.cmd_strength()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["scheduled"] is True
    assert output["happen_day"] == "20260716"
    assert captured == {"name": "Leg Circuit", "happen_day": "20260716", "sets": 2, "sort_no": 3}
