"""Client and local synthetic rehearsal engine for the Mekong Invited Pilot."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
from typing import Any
import urllib.error
import urllib.request
import uuid

DEFAULT_PILOT_API_URL = "https://api.cashclaw.cc"
MAX_PILOT_INVITES = 5
WEEKLY_MISSION_TARGET = 5
FEEDBACK_SLA_HOURS = 48


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def hash_invite_code(code: str) -> str:
    return hashlib.sha256(code.strip().upper().encode("utf-8")).hexdigest()


class PilotClientError(RuntimeError):
    """Raised when a pilot operation violates an invite, step-mode, or auth constraint."""

    def __init__(self, message: str, code: str = "PILOT_ERROR") -> None:
        super().__init__(message)
        self.code = code


class PilotClient:
    """Executes pilot invite, mission, feedback, and KPI operations remotely or locally."""

    def __init__(
        self, base_url: str | None = None, api_key: str | None = None,
        service_token: str | None = None, state_path: Path | None = None, offline: bool = False,
    ) -> None:
        self.base_url = (base_url or os.environ.get("MEKONG_PILOT_API_URL") or DEFAULT_PILOT_API_URL).rstrip("/")
        self.api_key = api_key or os.environ.get("MEKONG_API_KEY")
        self.service_token = service_token or os.environ.get("MEKONG_SERVICE_TOKEN")
        default_state = str(Path.home() / ".mekong" / "pilot_state.json")
        self.state_path = state_path or Path(os.environ.get("MEKONG_PILOT_STATE_PATH", default_state))
        self.offline = offline

    def _load_state(self) -> dict[str, Any]:
        if self.state_path.exists():
            try:
                return json.loads(self.state_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"invites": [], "tenants": [], "missions": [], "feedback": []}

    def _save_state(self, state: dict[str, Any]) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self.state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")

    def _http_json(self, method: str, path: str, payload: dict[str, Any] | None, token: str | None) -> dict[str, Any]:
        headers = {"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})}
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(f"{self.base_url}{path}", data=data, method=method, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise PilotClientError(f"HTTP {exc.code}: {exc.read().decode('utf-8', errors='ignore')}", code=f"HTTP_{exc.code}") from exc

    def issue_invite(self, partner_label: str = "Pilot Partner", max_invites: int = MAX_PILOT_INVITES) -> dict[str, Any]:
        if not self.offline and self.service_token:
            return self._http_json("POST", "/billing/invites", {"partner_label": partner_label}, self.service_token)
        state = self._load_state()
        if sum(1 for i in state["invites"] if i["status"] in ("active", "redeemed")) >= max_invites:
            raise PilotClientError(f"Pilot invite cap reached ({max_invites})", code="PILOT_INVITE_CAP_REACHED")
        raw_code = f"MK-PILOT-{secrets.token_hex(4).upper()}"
        invite = {
            "id": str(uuid.uuid4()), "code_hash": hash_invite_code(raw_code),
            "partner_label": partner_label, "status": "active",
            "redeemed_by_tenant_id": None, "created_at": _now_iso(),
        }
        state["invites"].append(invite)
        self._save_state(state)
        return {"invite_id": invite["id"], "invite_code": raw_code, "code_hash": invite["code_hash"], "partner_label": partner_label, "status": "active", "max_invites": max_invites}

    def redeem_invite(self, name: str, invite_code: str) -> dict[str, Any]:
        if not self.offline and not self.state_path.exists() and self.base_url != DEFAULT_PILOT_API_URL:
            return self._http_json("POST", "/billing/tenants", {"name": name, "invite_code": invite_code}, None)
        state = self._load_state()
        code_hash = hash_invite_code(invite_code)
        invite = next((i for i in state["invites"] if i["code_hash"] == code_hash), None)
        if not invite:
            raise PilotClientError("Invalid pilot invite code", code="PILOT_INVITE_INVALID")
        if invite["status"] != "active":
            raise PilotClientError("Pilot invite code already redeemed", code="PILOT_INVITE_ALREADY_REDEEMED")
        tenant_id, api_key = str(uuid.uuid4()), f"mk_pilot_{secrets.token_hex(16)}"
        invite["status"], invite["redeemed_by_tenant_id"] = "redeemed", tenant_id
        state["tenants"].append({"id": tenant_id, "name": name, "api_key": api_key, "credits": 10})
        self._save_state(state)
        return {"tenant_id": tenant_id, "name": name, "api_key": api_key, "tier": "free", "credits": 10}

    def submit_mission(self, goal: str, mode: str = "llm") -> dict[str, Any]:
        if mode != "llm":
            raise PilotClientError(f"Step mode '{mode}' is disabled during the LLM-only pilot", code="PILOT_LLM_ONLY")
        if not self.offline and self.api_key and not self.state_path.exists():
            return self._http_json("POST", "/v1/tasks", {"goal": goal}, self.api_key)
        state = self._load_state()
        tenant = state["tenants"][-1] if state["tenants"] else {"id": "synthetic-tenant", "credits": 10}
        mission = {
            "id": str(uuid.uuid4()), "tenant_id": tenant["id"], "goal": goal, "status": "completed",
            "credits_used": 1, "result": f"Synthetic pilot output for: {goal}",
            "created_at": _now_iso(), "completed_at": _now_iso(),
        }
        state["missions"].append(mission)
        self._save_state(state)
        return mission

    def submit_feedback(self, mission_id: str, rating: int, comment: str = "") -> dict[str, Any]:
        if rating < 1 or rating > 5:
            raise PilotClientError("Rating must be between 1 and 5", code="VALIDATION_ERROR")
        if not self.offline and self.api_key and not self.state_path.exists():
            return self._http_json("POST", f"/v1/tasks/{mission_id}/feedback", {"rating": rating, "comment": comment}, self.api_key)
        state = self._load_state()
        mission = next((m for m in state["missions"] if m["id"] == mission_id), None)
        if not mission:
            raise PilotClientError(f"Mission '{mission_id}' not found", code="NOT_FOUND")
        record = {
            "mission_id": mission_id, "tenant_id": mission["tenant_id"], "rating": rating,
            "comment": comment.strip() or None, "within_48h": True, "submitted_at": _now_iso(),
        }
        state["feedback"] = [f for f in state["feedback"] if f["mission_id"] != mission_id] + [record]
        self._save_state(state)
        return record

    def get_kpis(self) -> dict[str, Any]:
        if not self.offline and self.service_token and not self.state_path.exists():
            return self._http_json("GET", "/billing/pilot-kpis", None, self.service_token)
        state = self._load_state()
        missions, feedback = state["missions"], state["feedback"]
        redeemed = [i for i in state["invites"] if i["status"] == "redeemed"]
        avg_rating = round(sum(f["rating"] for f in feedback) / len(feedback), 2) if feedback else None
        return {
            "targets": {"max_partners": MAX_PILOT_INVITES, "missions_per_partner_per_week": WEEKLY_MISSION_TARGET, "feedback_sla_hours": FEEDBACK_SLA_HOURS},
            "totals": {
                "redeemed_partners": len(redeemed), "missions_submitted": len(missions),
                "missions_completed": sum(1 for m in missions if m["status"] == "completed"),
                "feedback_count": len(feedback), "feedback_within_48h_rate": 1.0, "average_rating": avg_rating,
            },
        }
