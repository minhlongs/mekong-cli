"""Load .claude/commands/*.md and match to classified tasks.

Maps task classifier output (agent_role, domain) to the best
matching command file. Feeds command content as system prompt
to the LLM, so output reflects Mekong's operational knowledge.
"""
from __future__ import annotations

import re
import logging
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

COMMANDS_DIR = Path(__file__).parent.parent.parent / ".claude" / "commands"


@dataclass
class Command:
    """Parsed command from .md file."""
    id: str
    path: Path
    description: str
    argument_hint: str
    allowed_tools: list[str]
    content: str


def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown."""
    if not text.startswith("---"):
        return {}, text
    end = text.find("---", 3)
    if end == -1:
        return {}, text
    frontmatter = {}
    for line in text[3:end].strip().split("\n"):
        if ":" in line:
            key, val = line.split(":", 1)
            frontmatter[key.strip().strip('"')] = val.strip().strip('"')
    return frontmatter, text[end + 3:].strip()


def load_all_commands() -> list[Command]:
    """Load all .claude/commands/*.md files."""
    if not COMMANDS_DIR.exists():
        logger.warning("Commands dir not found: %s", COMMANDS_DIR)
        return []

    commands = []
    for md_file in sorted(COMMANDS_DIR.glob("*.md")):
        try:
            text = md_file.read_text(encoding="utf-8")
            fm, body = _parse_frontmatter(text)
            commands.append(Command(
                id=md_file.stem,
                path=md_file,
                description=fm.get("description", ""),
                argument_hint=fm.get("argument-hint", ""),
                allowed_tools=[t.strip() for t in fm.get("allowed-tools", "").split(",") if t.strip()],
                content=text,
            ))
        except Exception as e:
            logger.warning("Failed to load %s: %s", md_file, e)

    logger.info("Loaded %d commands from %s", len(commands), COMMANDS_DIR)
    return commands


_COMMANDS: list[Command] | None = None


def get_commands() -> list[Command]:
    """Get cached command list."""
    global _COMMANDS
    if _COMMANDS is None:
        _COMMANDS = load_all_commands()
    return _COMMANDS


ROLE_PREFIXES: dict[str, list[str]] = {
    "cfo": ["accounting", "cashflow", "expense", "invoice", "finance", "revenue", "budget", "collections", "tax"],
    "cmo": ["marketing", "content", "campaign", "email", "seo", "brand", "social", "writer"],
    "cto": ["engineering", "deploy", "infra", "code-review", "architecture", "devops", "cook", "code"],
    "coo": ["ops", "process", "workflow", "onboarding", "hr", "recruiting"],
    "cro": ["sales", "pipeline", "deal", "crm", "outreach", "ae-", "sdr"],
    "cs": ["cs", "care", "ticket", "sla", "nps", "churn"],
    "sales": ["sales", "pipeline", "deal", "forecast", "sdr", "ae-"],
    "editor": ["content", "blog", "newsletter", "social", "writer"],
    "data": ["data", "analytics", "report", "metric", "dashboard"],
    "legal": ["legal", "contract", "compliance", "ip-", "nda", "privacy"],
}


def find_best_command(
    goal: str,
    agent_role: str = "",
    domain: str = "",
) -> Optional[Command]:
    """Find the best matching command for a classified goal.

    Strategy:
    1. Exact ID match if goal starts with /command-name
    2. Keyword match: goal words vs command ID and description
    3. Agent role prefix match (cfo → accounting, cmo → marketing)
    """
    commands = get_commands()
    if not commands:
        return None

    goal_lower = goal.lower().strip()

    # 1. Slash command: /accounting-daily "Q3 data"
    if goal_lower.startswith("/"):
        cmd_name = goal_lower.split()[0].lstrip("/").strip()
        for cmd in commands:
            if cmd.id == cmd_name:
                return cmd

    # 2. Score each command
    best_score = 0
    best_cmd = None
    goal_words = set(re.findall(r'\w+', goal_lower))
    role_keywords = ROLE_PREFIXES.get(agent_role, [])

    for cmd in commands:
        score = 0
        cmd_words = set(re.findall(r'\w+', f"{cmd.id} {cmd.description}".lower()))

        # Role prefix match
        for prefix in role_keywords:
            if cmd.id.startswith(prefix):
                score += 10

        # Keyword overlap
        overlap = goal_words & cmd_words
        score += len(overlap) * 2

        # Domain in description
        if domain and domain.lower() in cmd.description.lower():
            score += 5

        if score > best_score:
            best_score = score
            best_cmd = cmd

    if best_cmd and best_score >= 4:
        logger.info("Matched command: %s (score=%d) for goal: %s",
                     best_cmd.id, best_score, goal[:60])
        return best_cmd

    return None


def build_system_prompt(command: Command, goal: str) -> str:
    """Build system prompt from command content + goal context."""
    return f"""You are a Mekong AI OS operational agent.

## Your assigned command:
{command.content}

## Task:
Execute the above command for this specific request: {goal}

## Rules:
- Follow the command's pipeline and steps exactly
- Output structured, actionable results
- If the command specifies output format, use it
- Be specific to the user's goal, not generic
"""
