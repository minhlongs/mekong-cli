"""Example plugin C: echo-upper — CLI command that uppercases its input.

Demonstrates:
- A command plugin with explicit permission declarations.
- Multiple hooks in a single plugin class.
- ``register()`` calling both ``register_command`` and ``hook`` on the context.
"""

from __future__ import annotations

from typing import Any

from mekong.plugins import PluginContext, Result, command, hook, plugin
from mekong.plugins.types import HookSpec


@plugin(
    id="io.acme.echo-upper",
    name="Echo Upper",
    version="1.0.0",
    description="Uppercase the provided text. Demonstrates command + hook plugin.",
    author="acme",
    permissions=["stdio_write"],
    mcu_cost=0,
    entry_point="src.echo_upper.EchoUpperPlugin",
)
class EchoUpperPlugin:
    """Register ``upper`` command and log stdout writes."""

    @hook(HookSpec.AFTER_COMMAND, priority=90)
    def audit(self, ctx: PluginContext, command: str, result: Result) -> Result:
        ctx.log("echo-upper").info("cmd=%s status=%s", command, result.status.value)
        return Result.ok()

    @command("upper")
    def cmd_upper(self, ctx: PluginContext, args: dict[str, Any]) -> Result:
        text = str(args.get("text", ""))
        if not text:
            return Result.err("text argument is required", usage="upper --text 'hello'")
        upper = text.upper()
        return Result.ok(value={"original": text, "upper": upper})


def register(ctx: PluginContext) -> None:
    instance = EchoUpperPlugin()
    ctx.register_command("upper", instance.cmd_upper)
    ctx.hook(HookSpec.AFTER_COMMAND, instance.audit, priority=90)
