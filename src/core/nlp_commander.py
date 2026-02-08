"""
Mekong CLI - NLP Commander (Tôm Hùm Brain)

Uses Gemini 2.5 Pro to parse free-form Vietnamese/English messages
into structured ClaudeKit/Mekong CLI commands for CC CLI execution.

Flow:
  "làm auth cho agencyos đi"
    → Gemini parses intent
    → StructuredTask(intent="implement", project="agencyos-web", ...)
    → Antigravity picks up and coordinates CC CLI
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Optional

logger = logging.getLogger(__name__)

# Known projects in apps/ directory
KNOWN_PROJECTS = [
    "agencyos-web",
    "sophia-ai-factory",
    "openclaw-worker",
    "84tea",
    "wellnexus",
]

# ClaudeKit command vocabulary
CLAUDEKIT_COMMANDS = {
    "plan": "/plan",
    "plan_fast": "/plan:fast",
    "plan_hard": "/plan:hard",
    "implement": "/cook",
    "fix": "/debug",
    "debug": "/debug",
    "review": "/review",
    "test": "/test",
    "deploy": "/check-and-commit",
    "docs": "/docs:update",
    "status": "/status",
}

SYSTEM_PROMPT = """You are Tôm Hùm's brain — an AI command parser for the Mekong CLI system.

Your job: Parse a user's free-form message (Vietnamese or English) into a structured task.

## Available Projects (in apps/ directory):
- agencyos-web: Next.js 16 RaaS platform (Tailwind, Shadcn, Supabase)
- sophia-ai-factory: AI video content factory (Next.js, Telegram bot)
- openclaw-worker: Cloudflare Worker gateway
- 84tea: Tea e-commerce platform
- wellnexus: Wellness platform

## Intent Types:
- plan: User wants to plan/design something → generates /plan or /plan:hard
- implement: User wants to build/create/code something → generates /cook
- fix: User wants to fix a bug or issue → generates /debug
- review: User wants code review → generates /review
- test: User wants to run tests → generates /test
- deploy: User wants to deploy/commit → generates /check-and-commit
- refactor: User wants to refactor code → generates /cook with refactor focus
- status: User asks about system status (no CC CLI needed)

## Rules:
1. ALWAYS detect the target project if mentioned (even implicitly)
2. Generate a DETAILED cc_cli_prompt optimized for Claude Code CLI execution
3. The cc_cli_prompt should be specific, actionable, and include file paths when possible
4. Map to appropriate ClaudeKit commands
5. Set priority: "urgent" if user says gấp/urgent/now, otherwise "normal"
6. Respond ONLY with valid JSON, no markdown

## Output JSON format:
{
  "intent": "implement|plan|fix|review|test|deploy|refactor|status",
  "project": "agencyos-web" or null,
  "summary": "Brief 1-line summary of what user wants",
  "cc_cli_prompt": "Detailed prompt for CC CLI to execute...",
  "claudekit_commands": ["/plan:fast", "/cook"],
  "priority": "normal|urgent",
  "needs_confirmation": false
}"""


@dataclass
class StructuredTask:
    """Parsed NLP command → structured task for CC CLI."""

    intent: str = "implement"
    project: Optional[str] = None
    summary: str = ""
    cc_cli_prompt: str = ""
    claudekit_commands: List[str] = field(default_factory=list)
    priority: str = "normal"
    needs_confirmation: bool = False
    raw_message: str = ""
    parse_error: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


class NLPCommander:
    """Gemini-powered NLP → structured command parser."""

    def __init__(self) -> None:
        self._client = None

    def _get_client(self):
        """Lazy-load LLM client."""
        if self._client is None:
            from src.core.llm_client import get_client

            self._client = get_client()
        return self._client

    def parse(self, message: str) -> StructuredTask:
        """
        Parse free-form message into structured task.

        Args:
            message: User's natural language message (Vietnamese/English)

        Returns:
            StructuredTask with intent, project, cc_cli_prompt, etc.
        """
        client = self._get_client()

        if not client.is_available:
            return StructuredTask(
                raw_message=message,
                parse_error="Gemini offline — cannot parse NLP",
                summary=message,
                cc_cli_prompt=message,
                intent="implement",
            )

        try:
            response = client.chat(
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message},
                ],
                temperature=0.3,
                max_tokens=1024,
                json_mode=True,
            )

            # Parse JSON response
            content = response.content.strip()
            # Strip markdown code fences if present
            if content.startswith("```"):
                content = content.split("\n", 1)[1] if "\n" in content else content
                if content.endswith("```"):
                    content = content[:-3]
                content = content.strip()

            data = json.loads(content)

            task = StructuredTask(
                intent=data.get("intent", "implement"),
                project=data.get("project"),
                summary=data.get("summary", message[:60]),
                cc_cli_prompt=data.get("cc_cli_prompt", message),
                claudekit_commands=data.get("claudekit_commands", ["/cook"]),
                priority=data.get("priority", "normal"),
                needs_confirmation=data.get("needs_confirmation", False),
                raw_message=message,
            )

            # Validate project name
            if task.project and task.project not in KNOWN_PROJECTS:
                # Try fuzzy match
                for p in KNOWN_PROJECTS:
                    if (
                        task.project.lower() in p.lower()
                        or p.lower() in task.project.lower()
                    ):
                        task.project = p
                        break

            logger.info(
                f"NLP parsed: intent={task.intent}, project={task.project}, "
                f"summary={task.summary[:40]}"
            )
            return task

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Gemini JSON: {e}")
            return StructuredTask(
                raw_message=message,
                parse_error=f"JSON parse error: {e}",
                summary=message[:60],
                cc_cli_prompt=message,
                intent="implement",
            )
        except Exception as e:
            logger.error(f"NLP parse error: {e}")
            return StructuredTask(
                raw_message=message,
                parse_error=str(e),
                summary=message[:60],
                cc_cli_prompt=message,
                intent="implement",
            )

    def format_confirmation(self, task: StructuredTask) -> str:
        """Format parsed task for Telegram confirmation message."""
        intent_icons = {
            "plan": "📝",
            "implement": "🔨",
            "fix": "🔧",
            "debug": "🔧",
            "review": "👀",
            "test": "🧪",
            "deploy": "🚀",
            "refactor": "♻️",
            "status": "📊",
        }
        icon = intent_icons.get(task.intent, "🦞")
        project_str = f"\n📂 Project: `{task.project}`" if task.project else ""
        commands_str = (
            " → ".join(task.claudekit_commands) if task.claudekit_commands else ""
        )

        return (
            f"🧠 *Tôm Hùm hiểu:*\n\n"
            f"{icon} Intent: *{task.intent.upper()}*{project_str}\n"
            f"🎯 {task.summary}\n"
            f"⚙️ Commands: `{commands_str}`\n\n"
            f"⚡ Đang gửi cho Antigravity xử lý..."
        )


# Module-level singleton
_commander = None


def get_commander() -> NLPCommander:
    """Get or create NLP commander singleton."""
    global _commander
    if _commander is None:
        _commander = NLPCommander()
    return _commander


__all__ = ["NLPCommander", "StructuredTask", "get_commander"]
