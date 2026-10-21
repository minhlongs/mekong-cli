# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Activation Sync — Dashboard Webhook Bridge."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import hmac
import json
import logging
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional

import requests

from .raas_auth import RaaSAuthClient

logger = logging.getLogger(__name__)


class ActivationSync:
    """Dashboard Sync Webhook Bridge."""

    DASHBOARD_URL = os.getenv("AGENCYOS_DASHBOARD_URL", "https://www.mekongmind.com")
    SYNC_ENDPOINT = "/api/v1/dashboard/sync"
    MAX_RETRIES = 3
    RETRY_DELAY = 5

    def __init__(self, auth_client: Optional[RaaSAuthClient] = None):
        self.auth = auth_client or RaaSAuthClient()
        self._session = requests.Session()
        self._queue_file = Path.home() / ".mekong" / "sync_queue.json"
        self._ensure_mekong_dir()

    def _ensure_mekong_dir(self) -> None:
        self._queue_file.parent.mkdir(parents=True, exist_ok=True)

    def sync_activation(
        self, tenant_id: str, agency_id: str, tier: str,
        license_key: Optional[str] = None, features: Optional[list[str]] = None,
    ) -> bool:
        """Sync license activation to dashboard."""
        event = {
            "event_type": "license_activated",
            "tenant_id": tenant_id,
            "agency_id": agency_id,
            "tier": tier,
            "license_key": self._mask_key(license_key) if license_key else None,
            "features": features or [],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "idempotency_key": self._generate_idempotency_key(tenant_id, agency_id),
        }
        if not self._send_event(event):
            self._queue_event(event)
        return True

    def _send_event(self, event: Dict[str, Any]) -> bool:
        url = f"{self.DASHBOARD_URL}{self.SYNC_ENDPOINT}"
        try:
            session = self.auth.get_session()
            headers = {"Content-Type": "application/json", "User-Agent": "mekong-cli/0.2.0"}
            if session.authenticated and session.tenant and session.tenant.license_key:
                headers["Authorization"] = f"Bearer {session.tenant.license_key}"
            headers["X-Webhook-Signature"] = self._generate_signature(event)
            response = self._session.post(url, json=event, headers=headers, timeout=10)
            if response.status_code in (200, 201, 204):
                return True
            logger.warning("Dashboard sync failed: %s", response.status_code)
            return False
        except requests.exceptions.RequestException as e:
            logger.warning("Dashboard sync error: %s", e)
            return False

    def _queue_event(self, event: Dict[str, Any]) -> None:
        queue = self._load_queue()
        queue["events"].append({
            "event": event,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "retries": 0,
        })
        self._save_queue(queue)

    def _load_queue(self) -> Dict[str, Any]:
        if self._queue_file.exists():
            try:
                with open(self._queue_file, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"events": []}

    def _save_queue(self, queue: Dict[str, Any]) -> None:
        with open(self._queue_file, "w") as f:
            json.dump(queue, f, indent=2)

    def _generate_idempotency_key(self, tenant_id: str, agency_id: str) -> str:
        data = f"{tenant_id}:{agency_id}:{int(time.time() / 3600)}"
        return hashlib.sha256(data.encode()).hexdigest()[:32]

    def _generate_signature(self, event: Dict[str, Any]) -> str:
        secret = os.getenv("DASHBOARD_WEBHOOK_SECRET", "mekong-webhook-secret")
        payload = json.dumps(event, sort_keys=True)
        signature = hmac.new(secret.encode(), payload.encode(), hashlib.sha256).hexdigest()
        return f"sha256={signature}"

    def _mask_key(self, license_key: str) -> str:
        if len(license_key) > 12:
            return f"{license_key[:8]}...{license_key[-4:]}"
        return "(hidden)"

    def process_queue(self) -> int:
        queue = self._load_queue()
        processed = 0
        remaining_events = []
        for item in queue["events"]:
            if item["retries"] >= self.MAX_RETRIES:
                continue
            if self._send_event(item["event"]):
                processed += 1
            else:
                item["retries"] += 1
                remaining_events.append(item)
        queue["events"] = remaining_events
        self._save_queue(queue)
        return processed


_sync_instance: Optional[ActivationSync] = None


def get_activation_sync() -> ActivationSync:
    global _sync_instance
    if _sync_instance is None:
        _sync_instance = ActivationSync()
    return _sync_instance
