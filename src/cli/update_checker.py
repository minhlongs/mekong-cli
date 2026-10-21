# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""CLI Update Checker — RaaS Gateway Version Check."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from src.core.gateway_client import GatewayClient, get_gateway_client

console = Console()
CACHE_FILE, CACHE_TTL_HOURS, CHECK_TIMEOUT_SECONDS = "~/.mekong/update_check.json", 24, 2


@dataclass
class UpdateAvailable:
    current_version: str
    latest_version: str
    download_url: str
    checksum_url: str
    signature_url: str
    is_critical: bool
    is_security_update: bool
    release_notes: str
    released_at: str
    changelog_url: str


@dataclass
class UpdateCache:
    checked_at: datetime
    latest_version: Optional[str] = None
    update_available: bool = False
    update_info: Optional[dict[str, Any]] = None
    last_notified_version: Optional[str] = None

    @property
    def is_expired(self) -> bool:
        return datetime.now(timezone.utc) > (self.checked_at + timedelta(hours=CACHE_TTL_HOURS))

    @property
    def should_check(self) -> bool:
        return not self.checked_at or self.is_expired

    def to_dict(self) -> dict[str, Any]:
        return {"checked_at": self.checked_at.isoformat(), "latest_version": self.latest_version, "update_available": self.update_available, "update_info": self.update_info, "last_notified_version": self.last_notified_version}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "UpdateCache":
        return cls(checked_at=datetime.fromisoformat(data["checked_at"]), latest_version=data.get("latest_version"), update_available=data.get("update_available", False), update_info=data.get("update_info"), last_notified_version=data.get("last_notified_version"))


def _build_update(current: str, latest: str, data: dict[str, Any], force_critical: bool = False) -> UpdateAvailable:
    return UpdateAvailable(
        current, latest, data.get("download_url", ""), data.get("checksum_url", ""), data.get("signature_url", ""),
        force_critical or data.get("is_critical", False), data.get("is_security_update", False),
        data.get("release_notes", ""), data.get("released_at", ""), data.get("changelog_url", ""),
    )


class UpdateChecker:
    def __init__(self, gateway_client: Optional[GatewayClient] = None):
        self.gateway = gateway_client or get_gateway_client()
        self.cache_path = Path(CACHE_FILE).expanduser()
        self.cache = self._load_cache()

    def _ensure_cache_dir(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        os.chmod(self.cache_path.parent, 0o700)

    def _load_cache(self) -> UpdateCache:
        if not self.cache_path.exists():
            return UpdateCache(checked_at=datetime.min.replace(tzinfo=timezone.utc))
        try:
            return UpdateCache.from_dict(json.loads(self.cache_path.read_text()))
        except (json.JSONDecodeError, IOError, KeyError):
            return UpdateCache(checked_at=datetime.min.replace(tzinfo=timezone.utc))

    def _save_cache(self, cache: UpdateCache) -> None:
        self._ensure_cache_dir()
        self.cache_path.write_text(json.dumps(cache.to_dict(), indent=2))
        os.chmod(self.cache_path, 0o600)

    def should_check(self) -> bool:
        return False if os.getenv("MEKONG_NO_UPDATE_CHECK") else self.cache.should_check

    async def check_version(self) -> Optional[UpdateAvailable]:
        current = self.get_current_version()
        try:
            data = (await asyncio.wait_for(asyncio.to_thread(self.gateway.get, "/v1/cli/version"), timeout=CHECK_TIMEOUT_SECONDS)).data
            latest = data.get("latest_version", current)
            self.cache = UpdateCache(checked_at=datetime.now(timezone.utc), latest_version=latest, update_info=data)
            self._save_cache(self.cache)
            return _build_update(current, latest, data) if self._is_newer_version(latest, current) else None
        except Exception:
            return None

    def check_version_sync(self) -> Optional[UpdateAvailable]:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(self.check_version())

    def check_critical_update(self) -> Optional[UpdateAvailable]:
        update = self.check_version_sync()
        if update and update.is_critical:
            self._mark_critical_update_pending(update)
            return update
        return None

    def _mark_critical_update_pending(self, update: UpdateAvailable) -> None:
        self.cache.update_info = {**(self.cache.update_info or {}), "is_critical": True, "critical_pending": True, "critical_version": update.latest_version}
        self._save_cache(self.cache)
    def should_block_execution(self) -> bool:
        info = self.cache.update_info
        return bool(info and (info.get("critical_pending") or self.get_current_version() in info.get("critical_versions", [])))
    def get_critical_update_info(self) -> Optional[UpdateAvailable]:
        info = self.cache.update_info
        return _build_update(self.get_current_version(), info.get("critical_version", ""), info, force_critical=True) if info and info.get("critical_pending") else None
    def get_current_version(self) -> str:
        try:
            import importlib.metadata
            return importlib.metadata.version("mekong-cli")
        except importlib.metadata.PackageNotFoundError:
            return "0.0.0"
    def _is_newer_version(self, latest: str, current: str) -> bool:
        try:
            return tuple(map(int, latest.lstrip("v").split(".")[:3])) > tuple(map(int, current.lstrip("v").split(".")[:3]))
        except (ValueError, IndexError):
            return False

    def notify_if_available(self, update: Optional[UpdateAvailable]) -> None:
        if not update or self.cache.last_notified_version == update.latest_version:
            return
        msg_type = "🚨 CRITICAL" if update.is_critical else ("🔒 SECURITY" if update.is_security_update else "📦 UPDATE")
        console.print(f"\n[{self._get_color(update)}]{msg_type}[/]: mekong-cli {update.current_version} → {update.latest_version}")
        if update.release_notes:
            console.print(f"  {update.release_notes}")
        console.print(f"  Run: [bold]mekong update install[/bold] to upgrade\n  Changelog: {update.changelog_url}\n")
        self.cache.last_notified_version = update.latest_version
        self._save_cache(self.cache)

    def _get_color(self, update: UpdateAvailable) -> str:
        return "bold red" if update.is_critical else ("bold yellow" if update.is_security_update else "bold blue")

    def get_cache_status(self) -> dict[str, Any]:
        return {"cache_exists": self.cache_path.exists(), "checked_at": self.cache.checked_at.isoformat() if self.cache.checked_at else None, "is_expired": self.cache.is_expired, "should_check": self.should_check(), "latest_version": self.cache.latest_version, "update_available": self.cache.update_available}

_checker: Optional[UpdateChecker] = None


def get_update_checker() -> UpdateChecker:
    global _checker
    if _checker is None:
        _checker = UpdateChecker()
    return _checker


async def check_for_updates_async() -> Optional[UpdateAvailable]:
    checker = get_update_checker()
    return await checker.check_version() if checker.should_check() else None


def notify_update_available(update: Optional[UpdateAvailable]) -> None:
    if update:
        get_update_checker().notify_if_available(update)
