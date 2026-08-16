# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Example plugin B: timestamp — emits ISO-8601 current time on every hook.

Use case: audit trail of command executions.
Run with ``mekong plugin run timestamp`` after installation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from mekong.plugins import PluginContext, Result, hook, plugin
from mekong.plugins.types import HookSpec

logger = logging.getLogger(__name__)


@plugin(
    id="io.acme.timestamp",
    name="Timestamp",
    version="0.2.0",
    description="Spam the audit log with UTC timestamps on every lifecycle hook.",
    author="acme",
    permissions=["log_write"],
    entry_point="src.timestamp.TimestampPlugin",
)
class TimestampPlugin:
    """Registers BEFORE_COMMAND + AFTER_COMMAND hooks that print ISO-8601."""

    @hook(HookSpec.BEFORE_COMMAND, priority=20)
    def before(self, ctx: PluginContext, command: str, args: dict[str, Any]) -> Result:
        ts = datetime.now(timezone.utc).isoformat()
        ctx.log("timestamp").info("[%s] BEFORE %s args=%s", ts, command, args)
        return Result.ok(meta={"stamp": ts})

    @hook(HookSpec.AFTER_COMMAND, priority=20)
    def after(self, ctx: PluginContext, command: str, result: Result) -> Result:
        ts = datetime.now(timezone.utc).isoformat()
        ctx.log("timestamp").info("[%s] AFTER %s -> %s", ts, command, result.status.value)
        return Result.ok(meta={"stamp": ts, "result_status": result.status.value})

    @hook(HookSpec.ON_ERROR, priority=10)
    def on_error(self, ctx: PluginContext, exc: BaseException) -> Result:
        ts = datetime.now(timezone.utc).isoformat()
        ctx.log("timestamp").error("[%s] ERROR %s: %s", ts, type(exc).__name__, exc)
        return Result.ok(meta={"stamp": ts})


def register(ctx: PluginContext) -> None:
    """Entry point — subscribe the plugin's hooks via the context handle."""
    plugin = TimestampPlugin()
    ctx.hook(HookSpec.BEFORE_COMMAND, plugin.before, priority=20)
    ctx.hook(HookSpec.AFTER_COMMAND, plugin.after, priority=20)
    ctx.hook(HookSpec.ON_ERROR, plugin.on_error, priority=10)
