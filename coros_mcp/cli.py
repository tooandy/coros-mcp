"""CLI commands for Coros MCP Server."""
import asyncio
import getpass
import json
import sys
import time
from dataclasses import asdict

from coros_mcp.auth.storage import clear_token, get_token, is_keyring_available
from coros_mcp.coros_api import TOKEN_TTL_MS, get_stored_auth, login, login_mobile, try_auto_login


def _prompt_credentials() -> tuple[str, str, str]:
    """Prompt for email, password, and region. Returns (email, password, region)."""
    email = input("Email: ").strip()
    if not email:
        print("Error: email is required.")
        sys.exit(1)

    password = getpass.getpass("Password: ")
    if not password:
        print("Error: password is required.")
        sys.exit(1)

    print()
    print("Region options: eu, us, asia, cn")
    region = input("Region [eu]: ").strip().lower() or "eu"
    if region not in ("eu", "us", "asia", "cn"):
        print(f"Warning: unknown region '{region}', using it anyway.")
    return email, password, region


def cmd_auth() -> int:
    """Authenticate with Coros credentials and store token in keyring."""
    print("Coros MCP — Authentication")
    print()

    if is_keyring_available():
        print("Token will be stored in your system keyring.")
    else:
        print("System keyring not available — token will be stored in an encrypted local file.")
    print()

    email, password, region = _prompt_credentials()
    print()
    print("Authenticating…")
    try:
        auth = asyncio.run(login(email, password, region, skip_mobile=False))
        print(f"✓ Authenticated as user {auth.user_id} (region: {auth.region})")
        print("  Token stored securely. You only need to do this once.")
        return 0
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return 1


def cmd_auth_web() -> int:
    """Authenticate with Coros web API only (no mobile token)."""
    print("Coros MCP — Web API Authentication")
    print()

    email, password, region = _prompt_credentials()
    print()
    print("Authenticating (web only)…")
    try:
        auth = asyncio.run(login(email, password, region, skip_mobile=True))
        print(f"✓ Web API authenticated as user {auth.user_id} (region: {auth.region})")
        print("  Mobile token skipped — sleep data will not be available.")
        return 0
    except Exception as e:
        print(f"✗ Authentication failed: {e}")
        return 1


def cmd_auth_mobile() -> int:
    """Authenticate with Coros mobile API only."""
    print("Coros MCP — Mobile API Authentication")
    print()

    email, password, region = _prompt_credentials()
    print()
    print("Authenticating (mobile only)…")
    try:
        auth = asyncio.run(login_mobile(email, password, region))
        print(f"✓ Mobile API authenticated (region: {auth.region})")
        print("  Sleep data is now available.")
        return 0
    except Exception as e:
        print(f"✗ Mobile authentication failed: {e}")
        return 1


def cmd_auth_status() -> int:
    """Check whether valid tokens are stored."""
    auth = get_stored_auth()
    if auth is None:
        auth = asyncio.run(try_auto_login())
    if auth:
        age_ms = int(time.time() * 1000) - auth.timestamp
        remaining_hours = round((TOKEN_TTL_MS - age_ms) / 3_600_000, 1)

        # Web token status
        if auth.access_token:
            print(f"✓ Web API    — user_id: {auth.user_id}, region: {auth.region}, expires in ~{remaining_hours}h")
        else:
            print("✗ Web API    — not authenticated")

        # Mobile token status
        if auth.mobile_access_token:
            print("✓ Mobile API — token present (sleep data available)")
        elif auth.mobile_login_payload:
            print("⚠ Mobile API — token expired (can auto-refresh)")
        else:
            print("✗ Mobile API — not authenticated (run 'coros-mcp auth' or 'coros-mcp auth-mobile')")

        return 0
    else:
        result = get_token()
        if result.success:
            print("⚠ Token found but may be expired. Run 'coros-mcp auth' to re-authenticate.")
        else:
            print("✗ Not authenticated. Run 'coros-mcp auth' to log in.")
        return 1


def cmd_auth_clear() -> int:
    """Remove stored token from all backends."""
    result = clear_token()
    if result.success:
        print("✓ Token cleared.")
        return 0
    else:
        print(f"✗ {result.message}")
        return 1


def cmd_sync() -> int:
    """Full historical sync: pull all data from Coros and store locally."""
    import argparse
    from datetime import datetime, timedelta

    from coros_mcp.cache.sync import sync_all

    parser = argparse.ArgumentParser(
        prog="coros-mcp sync",
        description="Sync Coros data to the local cache.",
    )
    parser.add_argument(
        "--from",
        dest="start_day",
        metavar="YYYYMMDD",
        help="First date to sync (default: 2 years ago)",
    )
    parser.add_argument(
        "--to",
        dest="end_day",
        metavar="YYYYMMDD",
        help="Last date to sync (default: today)",
    )
    parsed = parser.parse_args(sys.argv[2:])
    start_day = parsed.start_day or (datetime.now() - timedelta(days=730)).strftime("%Y%m%d")
    end_day = parsed.end_day

    auth = get_stored_auth()
    if auth is None:
        auth = asyncio.run(try_auto_login())
    if auth is None:
        print("✗ Not authenticated. Set COROS_EMAIL and COROS_PASSWORD in .env, or run 'coros-mcp auth'.")
        return 1

    range_str = f"{start_day} → {end_day}" if end_day else f"{start_day} → today"
    print(f"Coros MCP — Sync ({range_str})")
    print("This may take a few minutes for a large date range.")
    print()

    async def _run():
        async def on_progress(msg: str):
            print(f"  {msg}")

        return await sync_all(auth, start_day, end_day=end_day, on_progress=on_progress)

    try:
        stats = asyncio.run(_run())
        print()
        print("✓ Sync complete")
        print(f"  Daily records : {stats['daily']}")
        print(f"  Sleep records : {stats['sleep']}")
        print(f"  Activities    : {stats['activities']}")
        if stats["errors"]:
            print(f"  Errors        : {len(stats['errors'])}")
            for e in stats["errors"]:
                print(f"    - {e}")
        c = stats.get("cache", {})
        print()
        print("Cache coverage:")
        for key in ("daily_records", "sleep_records", "activities"):
            s = c.get(key, {})
            print(f"  {key:16s}: {s.get('count', 0)} records  [{s.get('from', '—')} → {s.get('to', '—')}]")
        return 0
    except Exception as e:
        print(f"✗ Sync failed: {e}")
        return 1


def cmd_cache_status() -> int:
    """Show local cache coverage."""
    from coros_mcp.cache.store import cache_status, init_db
    init_db()
    c = cache_status()
    print(f"Cache: {c['db_path']}")
    print()
    for key in ("daily_records", "sleep_records", "activities"):
        s = c[key]
        if s["count"]:
            print(f"  {key:16s}: {s['count']:5d} records  [{s['from']} → {s['to']}]")
        else:
            print(f"  {key:16s}:     0 records  (empty — run 'coros-mcp sync')")
    return 0


def _load_json_arg(file_path: str | None, inline_json: str | None) -> dict:
    if inline_json is not None:
        data = inline_json
    elif file_path and file_path != "-":
        with open(file_path, encoding="utf-8") as handle:
            data = handle.read()
    else:
        data = sys.stdin.read()

    payload = json.loads(data)
    if not isinstance(payload, dict):
        raise ValueError("running workout input must be a JSON object")
    return payload


def _get_cli_auth():
    auth = get_stored_auth()
    if auth is None:
        auth = asyncio.run(try_auto_login())
    if auth is None:
        raise RuntimeError("Not authenticated. Set COROS_EMAIL and COROS_PASSWORD in .env, or run 'coros-mcp auth'.")
    return auth


def _running_workout_from_payload(payload: dict, *, template: bool = False):
    from coros_mcp.running import normalize_running_workout, validate_running_workout

    workout_payload = dict(payload)
    if template and not workout_payload.get("happen_day"):
        workout_payload["happen_day"] = "19700101"

    workout = normalize_running_workout(workout_payload)
    validate_running_workout(workout)
    return workout


def cmd_running() -> int:
    """Local running workout authoring helpers."""
    import argparse

    from coros_mcp import coros_api
    from coros_mcp.running import (
        compile_running_workout,
    )
    from coros_mcp.running.render import render_running_workout

    parser = argparse.ArgumentParser(
        prog="coros-mcp running",
        description="Validate, render, compile, schedule, or save semantic running workout JSON.",
    )
    parser.add_argument(
        "action",
        choices=(
            "validate",
            "render",
            "compile",
            "preview",
            "schedule",
            "save-template",
            "list-templates",
            "schedule-template",
        ),
        help="Local running workout operation to run.",
    )
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument(
        "--file",
        "-f",
        default="-",
        help="Path to a workout JSON file, or '-' for stdin (default).",
    )
    input_group.add_argument(
        "--json",
        dest="inline_json",
        help="Inline workout JSON payload.",
    )
    parser.add_argument("--render-preview", action="store_true", help="Include rendered_summary for write actions.")
    parser.add_argument("--workout-id", help="Running template ID for schedule-template.")
    parser.add_argument("--happen-day", help="YYYYMMDD date for schedule-template.")
    parser.add_argument("--sort-no", type=int, default=1, help="Order within the day for scheduling actions.")
    parsed = parser.parse_args(sys.argv[2:])

    try:
        if parsed.action == "list-templates":
            auth = _get_cli_auth()
            workouts = asyncio.run(coros_api.fetch_workout_templates(auth))
            running_workouts = [workout for workout in workouts if workout.get("sport_type") == 1]
            print(json.dumps(
                {
                    "ok": True,
                    "workouts": running_workouts,
                    "count": len(running_workouts),
                },
                ensure_ascii=False,
                indent=2,
            ))
            return 0

        if parsed.action == "schedule-template":
            if not parsed.workout_id or not parsed.happen_day:
                raise ValueError("schedule-template requires --workout-id and --happen-day")
            auth = _get_cli_auth()
            workouts = asyncio.run(coros_api.fetch_workout_templates(auth))
            template = next(
                (
                    workout
                    for workout in workouts
                    if workout.get("id") == str(parsed.workout_id) and workout.get("sport_type") == 1
                ),
                None,
            )
            if template is None:
                raise ValueError(f"Running workout template {parsed.workout_id} not found")
            response = asyncio.run(
                coros_api.schedule_workout_template(auth, parsed.workout_id, parsed.happen_day, parsed.sort_no)
            )
            print(json.dumps(
                {
                    "ok": True,
                    "scheduled": True,
                    "workout_id": parsed.workout_id,
                    "name": template.get("name"),
                    "happen_day": parsed.happen_day,
                    "response": response,
                },
                ensure_ascii=False,
                indent=2,
            ))
            return 0

        payload = _load_json_arg(parsed.file, parsed.inline_json)
        workout = _running_workout_from_payload(payload, template=parsed.action == "save-template")

        result: dict = {"ok": True}
        if parsed.action == "validate":
            result["valid"] = True
            result["normalized_workout"] = asdict(workout)
        elif parsed.action == "render":
            result["rendered_summary"] = render_running_workout(workout)
        elif parsed.action == "compile":
            result["program"] = compile_running_workout(workout)
        elif parsed.action == "preview":
            result["valid"] = True
            result["normalized_workout"] = asdict(workout)
            result["rendered_summary"] = render_running_workout(workout)
            result["program"] = compile_running_workout(workout)
        elif parsed.action == "schedule":
            auth = _get_cli_auth()
            program = compile_running_workout(workout)
            response = asyncio.run(
                coros_api._post_schedule_inline(auth, program, workout.happen_day, workout.sort_no)
            )
            result.update(
                {
                    "scheduled": True,
                    "name": workout.name,
                    "happen_day": workout.happen_day,
                    "steps_count": len(program["exercises"]),
                    "response": response,
                }
            )
            if parsed.render_preview:
                result["rendered_summary"] = render_running_workout(workout)
        elif parsed.action == "save-template":
            auth = _get_cli_auth()
            program = compile_running_workout(workout)
            workout_id = asyncio.run(coros_api.save_workout_program(auth, program))
            result.update(
                {
                    "saved": True,
                    "workout_id": workout_id,
                    "name": workout.name,
                    "steps_count": len(program["exercises"]),
                }
            )
            if parsed.render_preview:
                result["rendered_summary"] = render_running_workout(workout)

        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except Exception as exc:
        result = {"ok": False, "error": str(exc)}
        if parsed.action in ("validate", "preview"):
            result["valid"] = False
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 1


def cmd_serve() -> int:
    """Start the MCP server (stdio mode)."""
    from coros_mcp import server
    server.main()
    return 0


def cmd_help() -> int:
    print(
        """Coros MCP Server — CLI

Usage:
  coros-mcp serve                   Start the MCP server (used by Claude Code / OpenClaw)
  coros-mcp auth                    Authenticate with your Coros account (web + mobile)
  coros-mcp auth-web                Authenticate web API only (no sleep data)
  coros-mcp auth-mobile             Authenticate mobile API only (sleep data)
  coros-mcp auth-status             Check status of both tokens
  coros-mcp auth-clear              Remove stored token
  coros-mcp sync [--from YYYYMMDD] [--to YYYYMMDD]  Sync to local cache (default: 2 years → today)
  coros-mcp cache-status            Show local cache coverage
  coros-mcp running ACTION [--file workout.json]  Local running workout authoring helpers
  coros-mcp help                    Show this help message

Running ACTION:
  validate                           Validate semantic running workout JSON
  render                             Render a human-readable summary
  compile                            Compile to COROS workout payload
  preview                            Validate, render, and compile together
  schedule                           Schedule semantic running workout from JSON
  save-template                      Save semantic running workout JSON as a reusable template
  list-templates                     List reusable running workout templates
  schedule-template                  Schedule a reusable running template by ID
"""
    )
    return 0


def main() -> None:
    from dotenv import load_dotenv
    load_dotenv()

    command = sys.argv[1] if len(sys.argv) > 1 else "help"
    commands = {
        "serve": cmd_serve,
        "auth": cmd_auth,
        "auth-web": cmd_auth_web,
        "auth-mobile": cmd_auth_mobile,
        "auth-status": cmd_auth_status,
        "auth-clear": cmd_auth_clear,
        "sync": cmd_sync,
        "cache-status": cmd_cache_status,
        "running": cmd_running,
        "help": cmd_help,
        "--help": cmd_help,
        "-h": cmd_help,
    }
    if command in commands:
        sys.exit(commands[command]())
    else:
        print(f"Unknown command: {command}")
        print("Run 'coros-mcp help' for usage.")
        sys.exit(1)


if __name__ == "__main__":
    main()
