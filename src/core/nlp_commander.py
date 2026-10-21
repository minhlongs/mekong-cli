# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - NLP Commander (Tôm Hùm Brain)."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict, dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.providers.llm.client import LLMClient

logger = logging.getLogger(__name__)
KNOWN_PROJECTS = ["agencyos-web", "sophia-ai-factory", "openclaw-worker", "84tea", "wellnexus"]

SYSTEM_PROMPT = """You are Tôm Hùm's NLP brain — an AI command parser for a software development automation system.
Parse a user's free-form message (Vietnamese or English) into a structured JSON task for autonomous code execution.
Interpret commands through the 13 Strategic Chapters of Binh Pháp:
Ch.1 Planning (/plan), Ch.2 Resources (/runway), Ch.3 Stratagem (/muu-cong), Ch.4 Disposition (/hinh-the),
Ch.5 Momentum (/the-tran), Ch.6 Defense (/test, /hu-thuc), Ch.7 Maneuvering (/deploy), Ch.8 Variation (/cuu-bien),
Ch.9 Marching (/cook, /hanh-quan), Ch.10 Terrain (/dia-hinh), Ch.11 Nine Grounds (/cuu-dia),
Ch.12 Fire Attack (/hoa-cong), Ch.13 Espionage (/dung-gian).
Projects in apps/: agencyos-web, sophia-ai-factory, openclaw-worker, 84tea, wellnexus.
Intents: "plan", "implement", "fix", "review", "test", "deploy", "status", "strategy".
Respond ONLY with valid JSON containing keys: intent, project, summary, cc_cli_prompt, claudekit_commands, priority, needs_confirmation."""


@dataclass
class StructuredTask:
    intent: str = "implement"
    project: str | None = None
    summary: str = ""
    cc_cli_prompt: str = ""
    claudekit_commands: list[str] = field(default_factory=list)
    priority: str = "normal"
    needs_confirmation: bool = False
    raw_message: str = ""
    parse_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NLPCommander:
    """Gemini-powered NLP → structured command parser."""

    MEMORY_CONTEXT_MAX = 1000

    def __init__(self) -> None:
        self._client: LLMClient | None = None

    def _get_client(self) -> "LLMClient":
        if self._client is None:
            from src.providers.llm.client import get_client
            self._client = get_client()
        return self._client  # type: ignore[return-value]

    def parse(self, message: str) -> StructuredTask:
        client = self._get_client()
        if not client.is_available:
            return self._fallback_parse(message, error_detail="LLM offline")
        try:
            t0 = time.time()
            response = client.chat(
                messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": message}],
                temperature=0.3, max_tokens=1024, json_mode=True,
            )
            logger.info(f"NLP LLM call took {time.time() - t0:.1f}s (provider={client.mode})")
            content = response.content
            if not content or not content.strip():
                simplified = (
                    "Parse this into JSON with keys: intent, project, summary, "
                    f"cc_cli_prompt, claudekit_commands, priority, needs_confirmation.\n\nMessage: {message}"
                )
                content = client.chat(messages=[{"role": "user", "content": simplified}], temperature=0.2, max_tokens=1024, json_mode=True).content
                if not content or not content.strip():
                    return self._fallback_parse(message, error_detail=f"provider={client.mode}, both attempts empty")

            content = content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                content = ("\n".join(lines[1:]) if len(lines) > 1 else content).removesuffix("```").strip()

            data = json.loads(content)
            task = StructuredTask(
                intent=data.get("intent", "implement"), project=data.get("project"),
                summary=data.get("summary", message[:60]), cc_cli_prompt=data.get("cc_cli_prompt", message),
                claudekit_commands=data.get("claudekit_commands", ["/cook"]),
                priority=data.get("priority", "normal"), needs_confirmation=data.get("needs_confirmation", False),
                raw_message=message,
            )
            if task.project and task.project not in KNOWN_PROJECTS:
                for p in KNOWN_PROJECTS:
                    if task.project.lower() in p.lower() or p.lower() in task.project.lower():
                        task.project = p
                        break
            return task
        except Exception as e:
            logger.exception(f"NLP parse error: {e}")
            return self._fallback_parse(message, error_detail=f"exception: {str(e)[:80]}")

    def _fallback_parse(self, message: str, error_detail: str = "") -> StructuredTask:
        msg_lower = message.lower()
        project = next((p for p in KNOWN_PROJECTS if p in msg_lower or p.replace("-", "") in msg_lower or p.split("-")[0] in msg_lower), None)
        if not project:
            project = "agencyos-web" if "agency" in msg_lower else ("sophia-ai-factory" if "sophia" in msg_lower else ("84tea" if "tea" in msg_lower else None))

        intent, claudekit_commands = "implement", ["/cook"]
        rules = [
            (["plan", "lên kế hoạch", "nghiên cứu"], "plan", ["/plan fast"]),
            (["fix", "sửa", "bug", "lỗi", "debug"], "fix", ["/debug"]),
            (["review", "kiểm tra", "đánh giá", "xem giúp"], "review", ["/review"]),
            (["test", "kiểm thử"], "test", ["/test"]),
            (["deploy", "triển khai", "commit"], "deploy", ["/check-and-commit"]),
            (["status", "trạng thái", "tình hình"], "status", ["/status"]),
        ]
        for keywords, target_intent, cmds in rules:
            if any(w in msg_lower for w in keywords):
                intent, claudekit_commands = target_intent, cmds
                break

        return StructuredTask(
            intent=intent, project=project, summary=message[:60],
            cc_cli_prompt=f"{message} (Project: {project})" if project else message,
            claudekit_commands=claudekit_commands, priority="normal", needs_confirmation=True,
            raw_message=message, parse_error=error_detail or "Gemini returned empty -> Fallback used",
        )

    def format_confirmation(self, task: StructuredTask) -> str:
        intent_icons = {
            "plan": "📝", "implement": "🔨", "fix": "🔧", "debug": "🔧", "review": "👀",
            "test": "🧪", "deploy": "🚀", "refactor": "♻️", "status": "📊", "docs": "📚",
        }
        icon = intent_icons.get(task.intent, "🦞")
        project_str = f"\n📂 Project: `{task.project}`" if task.project else ""
        commands_str = " → ".join(task.claudekit_commands) if task.claudekit_commands else ""
        return (
            f"🧠 *Tôm Hùm hiểu:*\n\n{icon} Intent: *{task.intent.upper()}*{project_str}\n"
            f"🎯 {task.summary}\n⚙️ Commands: `{commands_str}`\n\n⚡ Sending to LLM provider..."
        )


_commander = None


def get_commander() -> NLPCommander:
    global _commander
    if _commander is None:
        _commander = NLPCommander()
    return _commander


__all__ = ["NLPCommander", "StructuredTask", "get_commander"]
