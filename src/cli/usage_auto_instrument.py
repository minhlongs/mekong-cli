# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Usage Auto Instrumentation — Phase 6."""

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class UsageEvent:
    """Usage event emitted after CLI command execution."""
    event_id: str
    event_type: str
    tenant_id: str
    license_key: str
    timestamp: str
    endpoint: str
    cli_version: str
    metadata: Dict[str, Any]


class UsageInstrumentor:
    """Auto-instruments CLI commands with usage tracking."""

    def __init__(self):
        self.gateway_url = os.getenv("RAAS_GATEWAY_URL", "https://api.cashclaw.cc")
        self.api_key = os.getenv("RAAS_LICENSE_KEY")
        self.tenant_id: Optional[str] = None
        self.cli_version = self._get_cli_version()
        self.usage_dir = Path.home() / ".mekong" / "usage"
        self.usage_dir.mkdir(parents=True, exist_ok=True)

    def _get_cli_version(self) -> str:
        try:
            from importlib.metadata import version
            return version("mekong-cli")
        except Exception:
            return "0.2.0-dev"

    def _get_tenant_id(self) -> Optional[str]:
        if self.tenant_id:
            return self.tenant_id
        try:
            from src.core.raas_auth import get_auth_client
            session = get_auth_client().get_session()
            if session.authenticated and session.tenant:
                self.tenant_id = session.tenant.tenant_id
                return self.tenant_id
        except Exception:
            pass
        if self.api_key:
            import hashlib
            self.tenant_id = hashlib.sha256(self.api_key.encode()).hexdigest()[:16]
            return self.tenant_id
        return None

    def _get_metadata(self, command: str) -> Dict[str, Any]:
        import platform
        import sys
        return {
            "os": platform.system(), "os_version": platform.version(),
            "python_version": sys.version.split()[0], "command": command,
            "is_ci": os.getenv("CI", "false").lower() == "true",
            "terminal": os.getenv("TERM", "unknown"),
        }

    def emit_event(self, command: str) -> Optional[str]:
        tenant_id = self._get_tenant_id()
        if not tenant_id or not self.api_key:
            logger.debug("No tenant ID or API key available, skipping usage event")
            return None

        event = UsageEvent(
            event_id=str(uuid.uuid4()), event_type="cli:command",
            tenant_id=tenant_id, license_key=self.api_key,
            timestamp=datetime.now(timezone.utc).isoformat(),
            endpoint=f"/v1/cli/{command}", cli_version=self.cli_version,
            metadata=self._get_metadata(command),
        )
        if not self._send_to_gateway(event):
            self._cache_event(event)
            logger.debug("Cached usage event %s for later sync", event.event_id)
            return None
        return event.event_id

    def _send_to_gateway(self, event: UsageEvent) -> bool:
        if not self._check_rate_limit():
            return False
        try:
            import requests
            headers = {
                "Authorization": f"Bearer {event.license_key}", "Content-Type": "application/json",
                "X-Idempotency-Key": event.event_id, "X-CLI-Version": self.cli_version,
            }
            resp = requests.post(f"{self.gateway_url}/v2/usage", json={"events": [asdict(event)]}, headers=headers, timeout=5)
            if resp.status_code == 200:
                self._update_rate_limit(resp.headers)
                return True
            if resp.status_code == 429:
                self._handle_rate_limit(resp.headers)
            return False
        except Exception as e:
            logger.debug("Failed to send usage event: %s", e)
            return False

    def _check_rate_limit(self) -> bool:
        try:
            from src.core.kv_store_client import get_kv_client
            return get_kv_client().get_rate_limit_state().remaining > 0
        except Exception:
            return True

    def _update_rate_limit(self, headers: dict) -> None:
        try:
            from src.core.kv_store_client import get_kv_client
            get_kv_client().update_rate_limit_state(
                int(headers.get("X-RateLimit-Remaining", 0)),
                int(headers.get("X-RateLimit-Limit", 0)),
                int(headers.get("X-RateLimit-Reset", 0)),
            )
        except Exception:
            pass

    def _handle_rate_limit(self, headers: dict) -> None:
        try:
            reset_in = int(headers.get("X-RateLimit-Reset", 0)) - int(datetime.now(timezone.utc).timestamp())
            if reset_in > 0:
                from src.core.kv_store_client import get_kv_client
                get_kv_client().set_rate_limit_reset(reset_in)
        except Exception:
            pass

    def _cache_event(self, event: UsageEvent) -> None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = self.usage_dir / f"usage_{timestamp}_{event.event_id[:8]}.json"
        with open(filepath, "w") as f:
            json.dump({"event": asdict(event), "cached_at": datetime.now(timezone.utc).isoformat(), "retry_count": 0}, f, indent=2)

    def get_cached_events(self, limit: int = 100) -> list:
        events = []
        for filepath in sorted(self.usage_dir.glob("usage_*.json"))[:limit]:
            try:
                with open(filepath, "r") as f:
                    events.append(json.load(f).get("event", {}))
            except Exception:
                continue
        return events

    def clear_cached_event(self, filepath: str) -> bool:
        try:
            Path(filepath).unlink()
            return True
        except Exception:
            return False


_instrumentor: Optional[UsageInstrumentor] = None


def get_instrumentor() -> UsageInstrumentor:
    global _instrumentor
    if _instrumentor is None:
        _instrumentor = UsageInstrumentor()
    return _instrumentor


def emit_usage_event(command: str) -> Optional[str]:
    if os.getenv("MEKONG_NO_USAGE_TRACKING", "").lower() == "true":
        return None
    return get_instrumentor().emit_event(command)
