"""Example plugin A: tiny Hello-World that registers a ``hello`` command.

Demonstrates the minimum idiomatic plugin structure using the SDK
decorators from ``mekong.plugins``:

- ``@plugin`` class-decorator sets the ``.mekong-plugin.json`` metadata.
- ``@hook`` optional hook subscription (register here for lifecycle events).
- ``command`` exposes a CLI handler that returns a ``Result``.

Directory layout for this plugin::

    plugins/hello-world/
        .mekong-plugin.json
        src/
            __init__.py   ← this file
"""

from __future__ import annotations

from typing import Any

from mekong.plugins import PluginContext, Result, command, hook, plugin
from mekong.plugins.types import HookSpec


@plugin(
    id="com.acme.hello-world",
    name="Hello World",
    version="0.1.0",
    description="Minimal demo plugin — greets the user.",
    author="acme",
    license="MIT",
    entry_point="src.hello_world.HelloWorldPlugin",
    mcu_cost=0,
)
class HelloWorldPlugin:
    """A very small reference plugin.

    register() below is the standard entry point name loaded by the
    PluginLoader.  The ``@plugin`` decorator stamps ``__plugin_meta__`` on
    the class so metadata can be discovered without executing the class.
    """

    label: str = "world"

    @hook(HookSpec.ON_STARTUP, priority=10)
    def on_startup(self, ctx: PluginContext) -> Result:
        ctx.log("hello-world").info("Hello World plugin initialised")
        return Result.ok()

    def greet(self, who: str = "world") -> dict[str, Any]:
        """Return a friendly greeting."""
        return {"greeting": f"Hello, {who}! From plugin com.acme.hello-world"}

    @command("greet")
    def cmd_greet(self, ctx: PluginContext, args: dict[str, Any]) -> Result:
        who = args.get("who", self.label)
        return Result.ok(value=self.greet(who))


def register(ctx: PluginContext) -> None:
    """Standard plugin entry point called by PluginLoader."""
    instance = HelloWorldPlugin()
    ctx.register_command("greet", instance.cmd_greet)
