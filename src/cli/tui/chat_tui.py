"""Textual chat TUI for Mekong CLI — streaming against OmniRoute."""

from __future__ import annotations

from typing import Any

from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.widgets import Footer, Header, Input, Markdown, Static

from .chat_config import DEFAULT_MODEL, MODELS
from .omni_client import OmniClient


class ChatTUI(App[None]):
    """Chat interface: user messages + assistant markdown, status bar, commands."""

    TITLE = "mk chat"

    BINDINGS = [("ctrl+c", "quit", "Quit")]

    SLASH_COMMANDS: dict[str, str] = {
        "/help": "Show available commands",
        "/model <alias|id>": "Switch model (default, minimax, kimi)",
        "/clear": "Clear conversation",
        "/quit": "Quit chat",
    }

    def __init__(self, model: str = DEFAULT_MODEL, project: str | None = None) -> None:
        super().__init__()
        self.model = model
        self.project = project
        self.history: list[dict[str, str]] = []
        self.client = OmniClient()
        self.streaming = False

    def compose(self) -> ComposeResult:
        yield Header()
        yield VerticalScroll(id="chat-scroll")
        yield Input(placeholder="Type a message, /help for commands", id="chat-input")
        yield Footer()

    def on_mount(self) -> None:
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        status = f"model: {self.model.split('/')[-1]}"
        if self.project:
            status += f" | project: {self.project}"
        scroll.mount(Static(f"[dim]{status}[/dim]"))
        if self.project:
            self.history.append(
                {"role": "system", "content": f"Project context: {self.project}. Answer concisely."}
            )
        self.query_one("#chat-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        self.query_one("#chat-input", Input).value = ""
        if not text:
            return
        if text.startswith("/"):
            self._handle_command(text)
            return
        self._send_message(text)

    def _handle_command(self, text: str) -> None:
        parts = text.split(maxsplit=1)
        cmd, arg = parts[0], (parts[1] if len(parts) > 1 else "")
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        if cmd == "/help":
            body = "\n".join(f"`{k}` — {v}" for k, v in self.SLASH_COMMANDS.items())
            scroll.mount(Markdown(body))
        elif cmd == "/model":
            if not arg:
                scroll.mount(Static("[yellow]usage: /model <alias|id>[/yellow]"))
                return
            try:
                self.model = self._resolve_model(arg)
                scroll.mount(Static(f"[green]model → {self.model.split('/')[-1]}[/green]"))
            except KeyError:
                scroll.mount(Static("[red]unknown alias — use default, minimax, kimi[/red]"))
        elif cmd == "/clear":
            self.history = []
            scroll.mount(Static("[dim]conversation cleared[/dim]"))
        elif cmd == "/quit":
            self.exit()
        else:
            scroll.mount(Static(f"[red]unknown command: {cmd} — /help[/red]"))
        scroll.scroll_end()

    def _resolve_model(self, alias: str) -> str:
        alias = alias.strip()
        if alias in MODELS:
            return MODELS[alias]
        if "/" in alias:
            return alias
        raise KeyError(alias)

    def _send_message(self, text: str) -> None:
        if self.streaming:
            return
        scroll = self.query_one("#chat-scroll", VerticalScroll)
        scroll.mount(Static(f"[bold cyan]you:[/bold cyan] {text}"))
        self.history.append({"role": "user", "content": text})
        self.history = self.history[-20:]  # cap
        self.streaming = True
        md = Markdown("...")
        scroll.mount(md)
        scroll.scroll_end()
        self.run_worker(self._stream(text, md), thread=False)

    async def _stream(self, text: str, md: Markdown) -> None:
        collected: list[str] = []
        banner_shown = False
        scroll = self.query_one("#chat-scroll", VerticalScroll)

        async def on_delta(chunk: Any) -> None:
            nonlocal banner_shown
            if chunk.text:
                collected.append(chunk.text)
                md.update("".join(collected))
                scroll.scroll_end()
            if (
                not banner_shown
                and chunk.actual_model
                and chunk.actual_model != self.model
            ):
                banner_shown = True
                scroll.mount(
                    Static(
                        f"[yellow]⚠ actual model: {chunk.actual_model}"
                        f"{' (' + chunk.provider + ')' if chunk.provider else ''}[/yellow]"
                    )
                )

        try:
            final = await self.client.stream_chat(self.model, self.history, on_delta)
            content = "".join(collected) or "(empty response)"
            md.update(content)
            if final.usage:
                usage = final.usage
                tokens = usage.get("total_tokens", 0)
                scroll.mount(Static(f"[dim]usage: {tokens} tokens[/dim]"))
            self.history.append({"role": "assistant", "content": content})
            self.history = self.history[-20:]
        except RuntimeError as exc:
            md.update(f"**Error:** {exc}")
        finally:
            self.streaming = False
            scroll.scroll_end()
