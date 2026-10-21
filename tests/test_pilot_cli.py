"""Unit and CLI integration tests for the `mekong pilot` command group."""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from typer.testing import CliRunner

from src.commands.pilot_command import pilot_app
from src.core.pilot_client import PilotClient, PilotClientError

runner = CliRunner()


def test_pilot_client_invite_cap_and_single_use_redemption(tmp_path: Path) -> None:
    state_file = tmp_path / "pilot_state.json"
    client = PilotClient(state_path=state_file, offline=True)

    issued_codes: list[str] = []
    for idx in range(5):
        res = client.issue_invite(partner_label=f"Partner {idx + 1}")
        assert res["status"] == "active"
        assert res["invite_code"].startswith("MK-PILOT-")
        issued_codes.append(res["invite_code"])

    # 6th invite must be blocked by 5-partner cap
    with pytest.raises(PilotClientError) as exc_info:
        client.issue_invite(partner_label="Partner 6")
    assert exc_info.value.code == "PILOT_INVITE_CAP_REACHED"

    # Redeem 1st invite -> 10 free credits
    tenant = client.redeem_invite(name="Partner 1", invite_code=issued_codes[0])
    assert tenant["credits"] == 10
    assert tenant["tier"] == "free"

    # Reusing same invite code must fail
    with pytest.raises(PilotClientError) as reuse_err:
        client.redeem_invite(name="Partner 1 Dup", invite_code=issued_codes[0])
    assert reuse_err.value.code == "PILOT_INVITE_ALREADY_REDEEMED"


def test_pilot_cli_commands_end_to_end(tmp_path: Path) -> None:
    state_str = str(tmp_path / "cli_pilot.json")

    # 1. Issue invite via CLI
    inv_res = runner.invoke(
        pilot_app,
        ["issue-invite", "--partner", "Alpha OA", "--state-file", state_str, "--offline", "--json"],
    )
    assert inv_res.exit_code == 0
    inv_data = json.loads(inv_res.stdout)
    code = inv_data["invite_code"]

    # 2. Redeem invite via CLI
    red_res = runner.invoke(
        pilot_app,
        ["redeem", "--name", "Alpha OA", "--code", code, "--state-file", state_str, "--offline", "--json"],
    )
    assert red_res.exit_code == 0
    red_data = json.loads(red_res.stdout)
    assert red_data["credits"] == 10

    # 3. Reject non-LLM mode (`shell`) in pilot
    bad_mode = runner.invoke(
        pilot_app,
        ["submit", "Run shell script", "--mode", "shell", "--state-file", state_str, "--offline"],
    )
    assert bad_mode.exit_code == 1

    # 4. Submit LLM-only mission
    sub_res = runner.invoke(
        pilot_app,
        ["submit", "Summarize synthetic Q1 tax checklist", "--state-file", state_str, "--offline", "--json"],
    )
    assert sub_res.exit_code == 0
    mission = json.loads(sub_res.stdout)
    assert mission["status"] == "completed"

    # 5. Submit 48h feedback
    fb_res = runner.invoke(
        pilot_app,
        [
            "feedback",
            mission["id"],
            "--rating",
            "5",
            "--comment",
            "Fast and accurate",
            "--state-file",
            state_str,
            "--offline",
            "--json",
        ],
    )
    assert fb_res.exit_code == 0
    fb_data = json.loads(fb_res.stdout)
    assert fb_data["within_48h"] is True
    assert fb_data["rating"] == 5

    # 6. Check operator KPIs
    kpi_res = runner.invoke(
        pilot_app,
        ["kpis", "--state-file", state_str, "--offline", "--json"],
    )
    assert kpi_res.exit_code == 0
    kpis = json.loads(kpi_res.stdout)
    assert kpis["totals"]["redeemed_partners"] == 1
    assert kpis["totals"]["missions_completed"] == 1
    assert kpis["totals"]["feedback_count"] == 1
    assert kpis["totals"]["average_rating"] == 5.0


def test_pilot_registered_in_root_cli() -> None:
    from src.cli.app_setup import build_app

    app = build_app()
    group_names = {g.name for g in app.registered_groups}
    assert "pilot" in group_names


def test_fastapi_invited_pilot_routes_end_to_end(tmp_path: Path) -> None:
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from src.api.vn_pilot_routes import router as vn_pilot_router

    app = FastAPI()
    app.include_router(vn_pilot_router)
    http = TestClient(app)
    headers = {"x-pilot-state-file": str(tmp_path / "api_pilot_state.json")}

    # 1. Issue invite
    inv = http.post("/v1/pilot/invites", json={"partner_label": "Beta Partner"}, headers=headers)
    assert inv.status_code == 201
    invite_code = inv.json()["invite_code"]

    # 2. Redeem invite -> 10 credits
    red = http.post("/v1/pilot/redeem", json={"name": "Beta Partner", "invite_code": invite_code}, headers=headers)
    assert red.status_code == 201
    assert red.json()["credits"] == 10

    # 3. Duplicate redeem blocked (409)
    dup = http.post("/v1/pilot/redeem", json={"name": "Beta Dup", "invite_code": invite_code}, headers=headers)
    assert dup.status_code == 409

    # 4. Non-LLM mission blocked (422)
    bad_mode = http.post("/v1/pilot/missions", json={"goal": "Run shell", "mode": "shell"}, headers=headers)
    assert bad_mode.status_code == 422

    # 5. Submit LLM mission -> completed
    mis = http.post("/v1/pilot/missions", json={"goal": "Draft synthetic VAT note", "mode": "llm"}, headers=headers)
    assert mis.status_code == 201
    mission_id = mis.json()["id"]

    # 6. Submit 48h feedback
    fb = http.post(
        f"/v1/pilot/missions/{mission_id}/feedback",
        json={"rating": 5, "comment": "Accurate synthetic VAT summary"},
        headers=headers,
    )
    assert fb.status_code == 200
    assert fb.json()["within_48h"] is True

    # 7. Query KPIs
    kpis = http.get("/v1/pilot/kpis", headers=headers)
    assert kpis.status_code == 200
    totals = kpis.json()["totals"]
    assert totals["redeemed_partners"] == 1
    assert totals["missions_completed"] == 1
    assert totals["average_rating"] == 5.0

