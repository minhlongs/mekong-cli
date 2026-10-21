# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tool and Browser agent step execution helpers for RecipeExecutor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from src.core.verifier import ExecutionResult

if TYPE_CHECKING:
    from rich.console import Console
    from src.core.circuit_breaker import CircuitBreaker
    from .parser import RecipeStep


class AgentStepsMixin:
    """Mixin providing ToolRegistry and BrowserAgent step execution."""

    console: Console
    _browse_breaker: CircuitBreaker

    def _execute_tool_step(self, step: RecipeStep) -> ExecutionResult:
        """Execute step via AGI v2 ToolRegistry."""
        tool_name = step.params.get("tool_name", "") if step.params else ""
        tool_args = step.params.get("tool_args", {}) if step.params else {}

        if not tool_name:
            tool_name = step.description.strip()

        self.console.print(f"[cyan][Tool] Executing:[/cyan] {tool_name}")

        try:
            from src.core.tool_registry import ToolRegistry

            registry = ToolRegistry()
            result = registry.execute(tool_name, tool_args)

            output = result.get("output", "")
            success = result.get("success", False)
            duration = result.get("duration_ms", 0)

            status_color = "green" if success else "red"
            self.console.print(
                f"[{status_color}]Tool "
                f"{'succeeded' if success else 'failed'} "
                f"({duration:.0f}ms)[/{status_color}]"
            )

            if output:
                self.console.print(
                    Panel(
                        str(output)[:1000],
                        title=f"Tool: {tool_name}",
                        border_style=status_color,
                        expand=False,
                    )
                )

            return ExecutionResult(
                exit_code=0 if success else 1,
                stdout=str(output),
                stderr=result.get("error", ""),
                metadata={
                    "mode": "tool",
                    "tool_name": tool_name,
                    "duration_ms": duration,
                },
            )

        except Exception as e:
            self.console.print(f"[bold red]Tool Error:[/bold red] {e!s}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                error=e,
                metadata={"mode": "tool", "tool_name": tool_name},
            )

    def _execute_browse_step(self, step: RecipeStep) -> ExecutionResult:
        """Execute step via AGI v2 BrowserAgent."""
        url = step.params.get("url", "") if step.params else ""
        browse_action = step.params.get("action", "analyze") if step.params else "analyze"

        if not url:
            url = step.description.strip()

        self.console.print(f"[cyan][Browse] {browse_action}:[/cyan] {url}")

        def _call_browse():
            from src.core.browser_agent import BrowserAgent

            agent = BrowserAgent()
            if browse_action == "check":
                return agent.check_status(url)
            if browse_action == "links":
                return agent.get_links(url)
            return agent.analyze_page(url)

        def _browse_fallback():
            self.console.print(
                "[yellow]Browse circuit open — step skipped (fallback)[/yellow]"
            )
            return ExecutionResult(
                exit_code=0,
                stdout="[SKIPPED] Circuit open",
                stderr="",
                metadata={"mode": "browse", "circuit_open": True, "url": url},
            )

        try:
            result = self._browse_breaker.call(_call_browse, fallback=_browse_fallback)
            if isinstance(result, ExecutionResult):
                return result
            if browse_action == "check":
                output = (
                    f"HTTP {getattr(result, 'status_code', 0)} "
                    f"({getattr(result, 'duration_ms', 0):.0f}ms)"
                )
            elif browse_action == "links":
                links = getattr(result, "links", [])
                output = f"Found {len(links)} links:\n" + "\n".join(links[:10])
            else:
                output = (
                    f"Title: {getattr(result, 'title', '')}\n"
                    f"Status: {getattr(result, 'status_code', 0)}\n"
                    f"Links: {len(getattr(result, 'links', []))}\n"
                    f"Load Time: {getattr(result, 'load_time_ms', 0):.0f}ms\n\n"
                    f"{getattr(result, 'text_content', '')[:500]}"
                )

            self.console.print(
                Panel(
                    output[:1000],
                    title=f"Browse: {url[:60]}",
                    border_style="cyan",
                    expand=False,
                )
            )

            return ExecutionResult(
                exit_code=0 if getattr(result, "success", False) else 1,
                stdout=output,
                stderr="",
                metadata={"mode": "browse", "url": url, "action": browse_action},
            )

        except Exception as e:
            self.console.print(f"[bold red]Browse Error:[/bold red] {e!s}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                error=e,
                metadata={"mode": "browse", "url": url},
            )
