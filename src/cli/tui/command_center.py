"""Textual Command Center — 4 tabs: Chat | OPC | Agents | OmniRoute.

Extends the chat TUI into a single-window command center.
Tab OPC connects to OpenOPC Office UI WebSocket (realtime snapshot + events +
approval escalation). Tab Agents controls tmux sessions on M1 Pro. Tab
OmniRoute polls quota/health/logs.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widgets import Footer, Header, Input, Static, TabbedContent, TabPane

from .chat_config import resolve_model
from .chat_tui import ChatTUI
from .opc_ws_client import OpcWSClient


class OpcTab(Vertical):
    """Tab OPC: WebSocket realtime — snapshot summary + event log + approval."""

    def __init__(self, ws: OpcWSClient, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.ws = ws
        self.pending_approvals: dict[str, dict[str, Any]] = {}

    def compose(self) -> ComposeResult:
        with VerticalScroll(id="opc-summary"):
            yield Static("connecting to OPC WS...", id="opc-summary-text")
        with VerticalScroll(id="opc-events"):
            yield Static("[dim]event log[/dim]", id="opc-events-text")

    def on_mount(self) -> None:
        self.run_worker(self._read_loop(), thread=False)

    async def _read_loop(self) -> None:
        self.ws.state.snapshot = {}

        async def on_snapshot(snap: dict[str, Any]) -> None:
            self._render_snapshot(snap)

        async def on_event(entry: dict[str, Any]) -> None:
            self._append_event(entry)

        self.ws._on_snapshot = on_snapshot  # noqa: SLF001
        self.ws._on_event = on_event  # noqa: SLF001
        for attempt in range(3):
            try:
                await self.ws.connect()
                self._render_snapshot(self.ws.state.snapshot)
                await self.ws.run()  # blocks until disconnect
                return
            except Exception as exc:
                self._set_summary(f"[red]WS error ({attempt + 1}/3): {exc}[/red]")
                await asyncio.sleep(3)
        self._set_summary("[red]OPC WS unavailable — is opc ui running? (ws-up.sh)[/red]")

    def _render_snapshot(self, snap: dict[str, Any]) -> None:
        project = snap.get("project_id", "?")
        mode = snap.get("exec_mode", "?")
        agents = snap.get("agents") or []
        n_agents = len(agents) if isinstance(agents, list) else "?"
        self._set_summary(
            f"[green]● connected[/green] | project: {project} | mode: {mode} | agents: {n_agents}"
        )

    def _set_summary(self, text: str) -> None:
        w = self.query_one("#opc-summary-text", Static)
        w.update(text)

    def _append_event(self, entry: dict[str, Any]) -> None:
        etype = entry.get("type", "?")
        payload = entry.get("payload") or {}
        # capture approvals
        if isinstance(payload, dict):
            esc_id = payload.get("escalation_id") or payload.get("approval_id")
            if esc_id and payload.get("message"):
                self.pending_approvals[esc_id] = payload
        text = f"[dim][{etype}][/dim] {json.dumps(payload)[:200]}"
        self.query_one("#opc-events-text", Static).update(text)


class AgentsTab(Vertical):
    """Tab Agents: tmux sessions on M1 Pro (interactive Claude/opencode)."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.selected: str = "claude"
        self._poll_worker: Any = None

    def compose(self) -> ComposeResult:
        with Horizontal(classes="agent-header"):
            yield Static("agents:", classes="agent-label")
            yield Static("claude / opencode — select with 1/2, spawn [s], stop [x], type below",
                         id="agent-hint")
        yield Static("", id="agent-status")
        with VerticalScroll(id="agent-pane"):
            yield Static("[dim](select agent, press s to spawn)[/dim]", id="agent-pane-text")
        yield Input(placeholder="keys to send to agent (Enter = send)", id="agent-input")

    def on_mount(self) -> None:
        self._poll_worker = self.set_interval(1.0, self._poll)

    def _poll(self) -> None:
        try:
            from .tmux_controller import capture, list_agents
        except Exception:
            return
        statuses = {a["id"]: a["status"] for a in list_agents()}
        text = " | ".join(f"{k}: {v}" for k, v in statuses.items())
        self.query_one("#agent-status", Static).update(f"[dim]{text}[/dim]")
        if statuses.get(self.selected) == "running":
            pane = capture(self.selected, 40)
            if pane:
                self.query_one("#agent-pane-text", Static).update(pane)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value
        self.query_one("#agent-input", Input).value = ""
        try:
            from .tmux_controller import send_enter, send_key
        except Exception:
            return
        if text:
            send_key(self.selected, text)
            send_enter(self.selected)
        else:
            send_enter(self.selected)

    def on_key(self, event) -> None:
        if event.key == "1":
            self.selected = "claude"
            self.query_one("#agent-hint", Static).update("selected: claude (spawn [s])")
            event.stop()
        elif event.key == "2":
            self.selected = "opencode"
            self.query_one("#agent-hint", Static).update("selected: opencode (spawn [s])")
            event.stop()
        elif event.key == "s":
            try:
                from .tmux_controller import spawn
            except Exception:
                return
            ok, msg = spawn(self.selected)
            self.query_one("#agent-status", Static).update(f"[green]{msg}[/green]" if ok else f"[red]{msg}[/red]")
            event.stop()
        elif event.key == "x":
            try:
                from .tmux_controller import stop
            except Exception:
                return
            ok, msg = stop(self.selected)
            self.query_one("#agent-status", Static).update(f"[yellow]{msg}[/yellow]" if ok else f"[red]{msg}[/red]")
            event.stop()


class OmniTab(Vertical):
    """Tab OmniRoute: quota + health + recent calls (poll via ssh)."""

    pass  # implemented in P3


class CommandCenter(ChatTUI):
    """4-tab command center — reuses chat logic from ChatTUI."""

    TITLE = "mk command center"

    def __init__(self, model: str | None = None, project: str | None = None) -> None:
        super().__init__(model=model or resolve_model(None), project=project)
        self.ws = OpcWSClient()
        self._active_tab = "chat"

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(initial="tab-chat"):
            with TabPane("Chat", id="tab-chat"):
                with VerticalScroll(id="chat-scroll"):
                    yield Static(f"[dim]model: {self.model.split('/')[-1]}[/dim]")
                yield Input(placeholder="message or /command", id="chat-input")
            with TabPane("OPC", id="tab-opc"):
                yield OpcTab(self.ws)
            with TabPane("Agents", id="tab-agents"):
                yield AgentsTab()
            with TabPane("OmniRoute", id="tab-omni"):
                yield OmniTab()
        yield Footer()

    def on_tabbed_content_tab_activated(self, event: TabbedContent.TabActivated) -> None:
        self._active_tab = str(event.tab.id or "")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        # chat input only exists in tab-chat; guard
        if self._active_tab != "tab-chat":
            return
        super().on_input_submitted(event)

    def on_unmount(self) -> None:
        try:
            asyncio.get_event_loop().run_until_complete(self.ws.close())
        except Exception:
            pass
