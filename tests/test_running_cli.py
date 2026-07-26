import json
from unittest.mock import patch

from coros_mcp import cli


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
