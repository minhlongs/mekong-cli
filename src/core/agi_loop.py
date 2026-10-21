# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI - AGI Infinite Loop (Tôm Hùm Self-Improvement Engine)."""
from __future__ import annotations
import asyncio
import json
import logging
import os
import signal
import time
from pathlib import Path
from typing import Any
logger = logging.getLogger(__name__)
HISTORY_PATH = Path.home() / ".mekong" / "agi_history.json"
IMPROVEMENT_AREAS = ["error handling and resilience", "test coverage and quality", "code documentation and comments", "performance optimization", "security hardening", "new Telegram commands for user convenience", "NeuralMemory integration depth", "NLP understanding accuracy", "logging and observability", "configuration management", "modular architecture refactoring", "API endpoint design", "graceful shutdown and recovery", "rate limiting and throttling", "user experience improvements"]
AGI_ASSESS_PROMPT = 'You are Tôm Hùm\'s Self-Improvement Engine. Analyze mekong-cli to find the SINGLE most impactful improvement.\n## Previously Completed Improvements (DO NOT REPEAT):\n{completed_improvements}\n## Focus Areas:\n{focus_areas}\n## Current Codebase Context:\n{memory_context}\nReturn JSON: {{"improvement_id": "short-kebab-case-id", "title": "Human readable title", "description": "What to improve and why", "cc_cli_prompt": "Exact prompt for CC CLI", "target_files": ["src/core/file.py"], "estimated_minutes": 3, "priority": "high|medium|low", "category": "focus area"}}'

class AGILoop:
    DEFAULT_COOLDOWN, MAX_CONSECUTIVE_FAILURES = 90, 3
    def __init__(self, cooldown: int = DEFAULT_COOLDOWN, telegram_notify: bool = True, max_iterations: int | None = None) -> None:
        self.cooldown, self.telegram_notify, self.max_iterations = cooldown, telegram_notify, max_iterations
        self.iteration, self.consecutive_failures, self._running, self._shutdown_event = 0, 0, False, None
        self._history = self._load_history()
        self.completed_improvements: list[str] = self._history.get("completed", [])
        self.start_time, self.last_success_time, self.approval_mode, self._pending_approvals = time.time(), None, "manual", set()
    @property
    def shutdown_event(self) -> asyncio.Event:
        if self._shutdown_event is None:
            self._shutdown_event = asyncio.Event()
        return self._shutdown_event
    def _load_history(self) -> dict[str, Any]:
        try:
            return dict(json.loads(HISTORY_PATH.read_text())) if HISTORY_PATH.exists() else {"completed": [], "blacklist": {}, "details": []}
        except (json.JSONDecodeError, OSError):
            return {"completed": [], "blacklist": {}, "details": []}
    def _save_history(self) -> None:
        HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._history["completed"], self._history["details"] = self._history["completed"][-100:], self._history["details"][-100:]
        HISTORY_PATH.write_text(json.dumps(self._history, indent=2))
    def _is_blacklisted(self, improvement_id: str) -> bool:
        bl = self._history.get("blacklist", {}).get(improvement_id, {})
        return (time.time() - float(bl.get("last", 0))) < 86400 if int(bl.get("count", 0)) >= 2 else False
    def _calculate_cooldown(self) -> int:
        if self.consecutive_failures == 0:
            streak = sum(1 for d in self._history.get("details", [])[-5:] if d.get("success"))
            return int(max(30, self.cooldown // 2)) if streak >= 3 else int(self.cooldown)
        return int(min(self.cooldown * (2 ** self.consecutive_failures), 600))
    def get_status(self) -> dict[str, Any]:
        details = self._history.get("details", [])
        total, successes = len(details), sum(1 for d in details if d.get("success"))
        return {"running": self._running, "iteration": self.iteration, "improvements": len(self.completed_improvements), "consecutive_failures": self.consecutive_failures, "success_rate": round((successes / total * 100) if total else 0, 1), "uptime_seconds": int(time.time() - self.start_time if self.start_time else 0), "last_improvement": details[-1] if details else None, "cooldown": self._calculate_cooldown(), "approval_mode": self.approval_mode, "pending_approvals": len(self._pending_approvals)}
    async def run_forever(self) -> None:
        self._running = True
        for sig in (signal.SIGINT, signal.SIGTERM):
            asyncio.get_event_loop().add_signal_handler(sig, self._handle_shutdown)
        while self._running and (not self.max_iterations or self.iteration < self.max_iterations):
            self.iteration += 1
            if self.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                await self._safe_sleep(300)
                self.consecutive_failures = 0
            try:
                improvement = await self._assess()
                if not improvement:
                    await self._safe_sleep(self.cooldown)
                    continue
                if self._is_blacklisted(improvement.get("improvement_id", "")):
                    continue
                imp_id, success = improvement.get("improvement_id", ""), await self._execute(improvement)
                await self._memorize(improvement, bool(success))
                await self._report(improvement, bool(success))
                if success is True:
                    self.consecutive_failures, self.last_success_time = 0, time.time()
                    self.completed_improvements.append(imp_id)
                    self._history["completed"] = self.completed_improvements
                    self._history["details"].append({"id": imp_id, "title": improvement.get("title", ""), "category": improvement.get("category", ""), "timestamp": time.time(), "success": True})
                elif success is False:
                    self.consecutive_failures += 1
                    entry = self._history.setdefault("blacklist", {}).setdefault(imp_id, {"count": 0, "last": 0})
                    entry["count"], entry["last"] = entry["count"] + 1, time.time()
                self._save_history()
            except Exception as e:
                self.consecutive_failures += 1
                await self._report_error(str(e))
            if self._running:
                await self._safe_sleep(self._calculate_cooldown())
    async def _assess(self) -> dict[str, Any] | None:
        memory_context = "No memory available"
        try:
            from src.core.memory_client import get_memory_client
            mem = get_memory_client()
            memory_context = (mem.query_memory("mekong-cli codebase improvements needed", depth=2) if mem.is_available else None) or memory_context
        except Exception:
            pass
        prompt = AGI_ASSESS_PROMPT.format(completed_improvements="\n".join(f"- {imp}" for imp in self.completed_improvements[-20:]) or "None yet", focus_areas="\n".join(f"- {area}" for area in IMPROVEMENT_AREAS), memory_context=memory_context[:3000])
        try:
            from src.providers.llm.client import get_client
            client = get_client()
            content = (client.chat(messages=[{"role": "user", "content": prompt}], temperature=0.7, max_tokens=2048, json_mode=True).content or "").strip() if client.is_available else ""
            content = "\n".join(content.split("\n")[1:]).removesuffix("```").strip() if content.startswith("```") else content
            return dict(json.loads(content)) if content else None
        except Exception:
            return None
    async def _execute(self, improvement: dict[str, Any]) -> bool | None:
        cc_prompt, imp_id = improvement.get("cc_cli_prompt", ""), improvement.get("improvement_id", "")
        if not cc_prompt or not self._approval_allowed(imp_id):
            return None
        try:
            from src.core.cc_spawner import get_spawner
            session, wait_start = await get_spawner().spawn(goal=cc_prompt, timeout=300, agent_role="cto"), time.time()
            while session.status.value == "running" and (time.time() - wait_start) < 310:
                await asyncio.sleep(5)
            return session.status.value == "completed"
        except Exception:
            return False
    async def _memorize(self, improvement: dict[str, Any], success: bool) -> None:
        try:
            from src.core.memory_client import get_memory_client
            mem = get_memory_client()
            if mem.is_available:
                mem.add_memory(f"AGI Loop #{self.iteration}: {'SUCCESS' if success else 'FAILED'} - {improvement.get('title', 'Unknown')}. Category: {improvement.get('category', 'unknown')}. Files: {', '.join(improvement.get('target_files', []))}.", metadata={"type": "agi_loop", "iteration": self.iteration, "success": success, "improvement_id": improvement.get("improvement_id", "unknown")})
        except Exception:
            pass
    async def _report(self, improvement: dict[str, Any], success: bool) -> None:
        if self.telegram_notify:
            await self._send_telegram(f"♾️ *AGI Loop #{self.iteration}*\n\n{'✅' if success else '❌'} *{improvement.get('title', 'Unknown')}*\n📂 Category: {improvement.get('category', 'unknown')}\n⏱ Completed improvements: {len(self.completed_improvements)}\n🔄 Consecutive failures: {self.consecutive_failures}")
    async def _report_error(self, error: str) -> None:
        if self.telegram_notify:
            await self._send_telegram(f"⚠️ *AGI Loop #{self.iteration} Error*\n\n```\n{error[:500]}\n```")
    async def _send_telegram(self, message: str) -> None:
        try:
            import requests  # type: ignore[import-untyped]
            token, chat_ids, config_path = os.getenv("MEKONG_TELEGRAM_TOKEN", ""), [], os.path.expanduser("~/.mekong/config.yaml")
            if os.path.exists(config_path):
                import yaml  # type: ignore[import-untyped]
                with open(config_path) as f:
                    chat_ids = ((yaml.safe_load(f) or {}).get("telegram", {})).get("chat_ids", [])
            chat_ids = chat_ids or ([int(os.getenv("MEKONG_CHAT_ID", "0"))] if os.getenv("MEKONG_CHAT_ID", "") else [])
            for cid in (chat_ids if token else []):
                requests.post(f"https://api.telegram.org/bot{token}/sendMessage", json={"chat_id": cid, "text": message, "parse_mode": "Markdown"}, timeout=10)
        except Exception:
            pass
    async def _safe_sleep(self, seconds: int) -> None:
        try:
            await asyncio.wait_for(self.shutdown_event.wait(), timeout=seconds)
        except TimeoutError:
            pass
    def _handle_shutdown(self) -> None:
        self._running = False
        if self._shutdown_event is not None:
            self._shutdown_event.set()
    def stop(self) -> None:
        self._handle_shutdown()
    def approve_improvement(self, improvement_id: str) -> bool:
        added = bool(improvement_id and improvement_id not in self._pending_approvals)
        self._pending_approvals.update((improvement_id,) if added else ())
        return added
    def deny_improvement(self, improvement_id: str) -> bool:
        removed = improvement_id in self._pending_approvals
        self._pending_approvals.discard(improvement_id)
        return removed
    def _approval_allowed(self, improvement_id: str) -> bool:
        return True if self.approval_mode == "auto" else improvement_id in self._pending_approvals


_agi_loop: AGILoop | None = None
def get_agi_loop() -> AGILoop:
    global _agi_loop
    _agi_loop = _agi_loop or AGILoop()
    return _agi_loop
async def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [AGI] %(message)s", datefmt="%H:%M:%S")
    await AGILoop(cooldown=90, telegram_notify=True).run_forever()
if __name__ == "__main__":
    asyncio.run(main())
