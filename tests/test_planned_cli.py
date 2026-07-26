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


def test_planned_cli_list_outputs_schedule(capsys, monkeypatch):
    async def fake_fetch_schedule(auth, start_day, end_day):
        return {"entities": [{"idInPlan": 1}], "programs": []}

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "fetch_schedule", fake_fetch_schedule)

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "planned", "list", "--from", "20260701", "--to", "20260707"],
    ):
        result = cli.cmd_planned()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["ok"] is True
    assert output["count"] == 1
    assert output["date_range"] == "20260701 - 20260707"


def test_planned_cli_remove_calls_api(capsys, monkeypatch):
    captured = {}

    async def fake_remove_scheduled_workout(auth, plan_id, id_in_plan, plan_program_id):
        captured["plan_id"] = plan_id
        captured["id_in_plan"] = id_in_plan
        captured["plan_program_id"] = plan_program_id

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "remove_scheduled_workout", fake_remove_scheduled_workout)

    with patch.object(
        cli.sys,
        "argv",
        [
            "coros-mcp",
            "planned",
            "remove",
            "--plan-id",
            "plan-1",
            "--id-in-plan",
            "42",
            "--plan-program-id",
            "program-42",
        ],
    ):
        result = cli.cmd_planned()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["removed"] is True
    assert captured == {
        "plan_id": "plan-1",
        "id_in_plan": "42",
        "plan_program_id": "program-42",
    }


def test_planned_cli_calculate_outputs_updated_program(capsys, monkeypatch):
    program = {"name": "Run", "duration": 1}

    async def fake_calculate_workout_program(auth, program):
        return {"planDuration": 120}

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "calculate_workout_program", fake_calculate_workout_program)

    with patch.object(
        cli.sys,
        "argv",
        ["coros-mcp", "planned", "calculate", "--program-json", json.dumps(program)],
    ):
        result = cli.cmd_planned()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["calculation"] == {"planDuration": 120}
    assert output["program"]["duration"] == 120
    assert output["program"]["estimatedTime"] == 120


def test_planned_cli_update_calls_api_with_raw_payloads(capsys, monkeypatch):
    captured = {}
    entity = {"planId": "plan-1", "idInPlan": "42"}
    program = {"planId": "plan-1", "idInPlan": "42"}

    async def fake_update_scheduled_workout(auth, entity, program, version_object):
        captured["entity"] = entity
        captured["program"] = program
        captured["version_object"] = version_object

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "update_scheduled_workout", fake_update_scheduled_workout)

    with patch.object(
        cli.sys,
        "argv",
        [
            "coros-mcp",
            "planned",
            "update",
            "--entity-json",
            json.dumps(entity),
            "--program-json",
            json.dumps(program),
        ],
    ):
        result = cli.cmd_planned()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["updated"] is True
    assert captured == {"entity": entity, "program": program, "version_object": None}


def test_planned_cli_add_calls_api_with_raw_payloads(capsys, monkeypatch):
    captured = {}
    entity = {"happenDay": "20260715", "idInPlan": "42"}
    program = {"idInPlan": "42"}

    async def fake_add_planned_workout(auth, entity, program, version_object):
        captured["entity"] = entity
        captured["program"] = program
        captured["version_object"] = version_object

    monkeypatch.setattr(cli, "get_stored_auth", _auth)
    monkeypatch.setattr(coros_api, "add_planned_workout", fake_add_planned_workout)

    with patch.object(
        cli.sys,
        "argv",
        [
            "coros-mcp",
            "planned",
            "add",
            "--entity-json",
            json.dumps(entity),
            "--program-json",
            json.dumps(program),
        ],
    ):
        result = cli.cmd_planned()

    output = json.loads(capsys.readouterr().out)

    assert result == 0
    assert output["added"] is True
    assert output["happen_day"] == "20260715"
    assert captured == {"entity": entity, "program": program, "version_object": None}


def test_planned_cli_missing_required_args_returns_json_error(capsys, monkeypatch):
    monkeypatch.setattr(cli, "get_stored_auth", _auth)

    with patch.object(cli.sys, "argv", ["coros-mcp", "planned", "remove", "--plan-id", "plan-1"]):
        result = cli.cmd_planned()

    output = json.loads(capsys.readouterr().out)

    assert result == 1
    assert output["ok"] is False
    assert "--id-in-plan" in output["error"]
