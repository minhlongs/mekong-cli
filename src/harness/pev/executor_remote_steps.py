# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Remote step execution helpers (LLM and HTTP API) for RecipeExecutor."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.panel import Panel

from src.core.verifier import ExecutionResult

if TYPE_CHECKING:
    from rich.console import Console
    from src.core.circuit_breaker import CircuitBreaker
    from .parser import RecipeStep


class RemoteStepsMixin:
    """Mixin providing LLM and HTTP API step execution for RecipeExecutor."""

    console: Console
    _llm_breaker: CircuitBreaker
    _api_breaker: CircuitBreaker

    def _execute_llm_step(self, step: RecipeStep) -> ExecutionResult:
        """Execute LLM generation step via Antigravity Proxy or OpenAI."""
        from src.providers.llm.client import get_client

        self.console.print(f"[cyan][LLM] Generating:[/cyan] {step.description}")

        client = get_client()
        if not client.is_available:
            self.console.print("[yellow]LLM offline — skipping step[/yellow]")
            return ExecutionResult(
                exit_code=0,
                stdout="[SKIPPED] LLM offline",
                stderr="",
                metadata={"mode": "llm", "skipped": True},
            )

        try:
            prompt = step.description
            system_prompt = step.params.get("system", "") if step.params else ""

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            def _call_llm():
                return client.chat(messages)

            def _llm_fallback():
                self.console.print(
                    "[yellow]LLM circuit open — step skipped (fallback)[/yellow]"
                )
                return ExecutionResult(
                    exit_code=0,
                    stdout="[SKIPPED] Circuit open",
                    stderr="",
                    metadata={"mode": "llm", "circuit_open": True},
                )

            response = self._llm_breaker.call(_call_llm, fallback=_llm_fallback)
            if isinstance(response, ExecutionResult):
                return response
            output = response.content[:2000]
            self.console.print(
                Panel(
                    output,
                    title=f"LLM Output ({response.model})",
                    border_style="cyan",
                    expand=False,
                )
            )
            return ExecutionResult(
                exit_code=0,
                stdout=response.content,
                stderr="",
                metadata={"mode": "llm", "model": response.model},
            )

        except Exception as e:
            self.console.print(f"[bold red]LLM Error:[/bold red] {e!s}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                error=e,
                metadata={"mode": "llm"},
            )

    def _execute_api_step(self, step: RecipeStep) -> ExecutionResult:
        """Execute API call step."""
        import requests as req

        url = step.params.get("url", "") if step.params else ""
        method = (step.params.get("method", "GET") if step.params else "GET").upper()
        body = step.params.get("body", None) if step.params else None
        headers = step.params.get("headers", {}) if step.params else {}

        if not url:
            self.console.print("[yellow]No URL specified — skipping API step[/yellow]")
            return ExecutionResult(
                exit_code=0,
                stdout="[SKIPPED] No URL",
                stderr="",
                metadata={"mode": "api", "skipped": True},
            )

        self.console.print(f"[cyan][API] {method}:[/cyan] {url}")

        def _call_api():
            return req.request(method, url, json=body, headers=headers, timeout=30)

        def _api_fallback():
            self.console.print(
                "[yellow]API circuit open — step skipped (fallback)[/yellow]"
            )
            return ExecutionResult(
                exit_code=0,
                stdout="[SKIPPED] Circuit open",
                stderr="",
                metadata={"mode": "api", "circuit_open": True, "url": url},
            )

        try:
            response = self._api_breaker.call(_call_api, fallback=_api_fallback)
            if isinstance(response, ExecutionResult):
                return response
            status_color = "green" if response.ok else "red"
            self.console.print(
                f"[{status_color}]Status: {response.status_code}[/{status_color}]"
            )

            preview = response.text[:1000] if response.text else ""
            if preview:
                self.console.print(
                    Panel(preview, title="Response", border_style="dim", expand=False)
                )

            return ExecutionResult(
                exit_code=0 if response.ok else 1,
                stdout=response.text or "",
                stderr="" if response.ok else f"HTTP {response.status_code}",
                metadata={"mode": "api", "status_code": response.status_code, "url": url},
            )

        except req.exceptions.RequestException as e:
            self.console.print(f"[bold red]API Error:[/bold red] {e!s}")
            return ExecutionResult(
                exit_code=1,
                stdout="",
                stderr=str(e),
                error=e,
                metadata={"mode": "api", "url": url},
            )
