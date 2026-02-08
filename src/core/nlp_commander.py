"""
Mekong CLI - NLP Commander (Tôm Hùm Brain)

Uses Gemini 2.5 Pro to parse free-form Vietnamese/English messages
into structured ClaudeKit/Mekong CLI commands for CC CLI execution.
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

SYSTEM_PROMPT = """You are Tôm Hùm's NLP brain — an AI command parser for a software development automation system.

Your job: Parse a user's free-form message (Vietnamese or English) into a structured JSON task for autonomous code execution.

## Context: Mekong CLI + ClaudeKit Engineer

The user runs a monorepo with these projects in apps/:
- agencyos-web: Next.js 16 RaaS platform (Tailwind v4, Shadcn/UI, Supabase auth)
- sophia-ai-factory: AI video content factory (Next.js, Telegram bot, Supabase, Polar.sh payments)
- openclaw-worker: Cloudflare Worker API gateway
- 84tea: Tea e-commerce (Next.js)
- wellnexus: Wellness platform (Next.js, PayOS payments, i18n)

## ClaudeKit Engineer Commands (50+ available):

### Planning:
- /plan [description] — Create implementation plan
- /plan:fast [description] — Quick planning for simple tasks
- /plan:hard [complex feature] — Detailed planning with deep research
- /plan:two [description] — Plan with 2 alternative approaches

### Implementation:
- /cook [description] — Build/implement features end-to-end
- /coding-level [level] — Set code complexity (junior/mid/senior)

### Quality:
- /review — Review entire codebase
- /review:codebase — Parallel codebase review
- /test — Run test suite
- /test:ui — Run UI tests
- /debug [issue] — Debug and fix issues

### Git & Deploy:
- /check-and-commit — Check quality and commit
- /worktree [feature] — Create git worktree branch

### Documentation:
- /docs — Manage project documentation
- /docs:init — First-time documentation setup
- /docs:update — Update documentation after changes

### Status:
- /status — Get system status
- /watzup — Get project status overview

## Intent Classification:

Map the user's message to one of these intents:
- "plan" — User wants to plan/design/architect something. Use /plan or /plan:hard
- "implement" — User wants to build/create/code/make something. Use /cook
- "fix" — User wants to fix a bug, error, or issue. Use /debug
- "review" — User wants code review or architecture review. Use /review
- "test" — User wants to test or validate. Use /test
- "deploy" — User wants to deploy, commit, push. Use /check-and-commit
- "refactor" — User wants to refactor or restructure. Use /cook with refactor goal
- "docs" — User wants to update docs. Use /docs:update
- "status" — User asks about system/project status. No CC CLI needed.

## Critical Rules:
1. ALWAYS detect the target project from context (even implicitly via keywords like "sophia", "agency", "tea", "well")
2. Generate a DETAILED cc_cli_prompt — this prompt will be sent to Claude Code CLI to execute autonomously
3. The cc_cli_prompt must be specific: mention file paths, frameworks, libraries to use
4. Include relevant technical context (Next.js 16, Tailwind v4, Supabase, etc.)
5. Map to the BEST ClaudeKit command(s) for the task
6. Set priority: "urgent" if user says gấp/urgent/asap/now, otherwise "normal"
7. If the user's message is ambiguous, set needs_confirmation=true
8. RESPOND ONLY WITH VALID JSON — no markdown, no explanation

## Output JSON:
{
  "intent": "implement",
  "project": "agencyos-web",
  "summary": "Build authentication module with Supabase",
  "cc_cli_prompt": "In the Next.js 16 app at apps/agencyos-web, create a complete Supabase authentication module: 1) lib/supabase/client.ts with createBrowserClient, 2) lib/supabase/server.ts with createServerClient using cookies, 3) app/auth/login/page.tsx with email/password form using signInWithPassword, 4) app/auth/signup/page.tsx with registration form. Use @supabase/ssr for server-side auth. Add middleware.ts for route protection.",
  "claudekit_commands": ["/plan:fast Build Supabase auth", "/cook implement Supabase auth module"],
  "priority": "normal",
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
        """Parse free-form message into structured task."""
        client = self._get_client()

        if not client.is_available:
            return StructuredTask(
                raw_message=message,
                parse_error="Gemini offline",
                summary=message[:60],
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

            # Guard against None content
            content = response.content
            if not content:
                return StructuredTask(
                    raw_message=message,
                    parse_error="Gemini returned empty response",
                    summary=message[:60],
                    cc_cli_prompt=message,
                    intent="implement",
                )

            content = content.strip()

            # Strip markdown code fences if present
            if content.startswith("```"):
                lines = content.split("\n")
                content = "\n".join(lines[1:])
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
                for p in KNOWN_PROJECTS:
                    if (
                        task.project.lower() in p.lower()
                        or p.lower() in task.project.lower()
                    ):
                        task.project = p
                        break

            logger.info(f"NLP parsed: intent={task.intent}, project={task.project}")
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
            "docs": "📚",
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


# Singleton
_commander = None


def get_commander() -> NLPCommander:
    """Get or create NLP commander singleton."""
    global _commander
    if _commander is None:
        _commander = NLPCommander()
    return _commander


__all__ = ["NLPCommander", "StructuredTask", "get_commander"]
